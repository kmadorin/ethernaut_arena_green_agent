"""Green Agent executor for AgentBeats framework using official A2A SDK."""

from abc import abstractmethod
from pydantic import ValidationError

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InvalidParamsError,
    Task,
    TaskState,
    UnsupportedOperationError,
    InternalError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from agentbeats.models import EvalRequest


class GreenAgent:
    """Abstract base class for green agents (evaluators).

    Green agents orchestrate evaluations by:
    1. Validating evaluation requests
    2. Managing the evaluation environment
    3. Communicating with purple agents (participants)
    4. Collecting and returning results
    """

    @abstractmethod
    async def run_eval(self, request: EvalRequest, updater: TaskUpdater) -> None:
        """Run the evaluation.

        Args:
            request: Evaluation request with participants and config
            updater: Task updater for reporting progress and results
        """
        pass

    @abstractmethod
    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        """Validate the evaluation request.

        Args:
            request: Evaluation request to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass


class GreenExecutor(AgentExecutor):
    """A2A server executor that wraps a GreenAgent.

    This class handles the A2A protocol, parsing requests,
    and delegating to the GreenAgent implementation.
    """

    def __init__(self, green_agent: GreenAgent):
        """Initialize the executor.

        Args:
            green_agent: The green agent implementation to execute
        """
        self.agent = green_agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute an evaluation request via A2A protocol.

        Args:
            context: Request context from A2A framework
            event_queue: Event queue for status updates

        Raises:
            ServerError: If request is invalid or execution fails
        """
        request_text = context.get_user_input()
        try:
            req: EvalRequest = EvalRequest.model_validate_json(request_text)
            ok, msg = self.agent.validate_request(req)
            if not ok:
                raise ServerError(error=InvalidParamsError(message=msg))
        except ValidationError as e:
            raise ServerError(error=InvalidParamsError(message=e.json()))

        msg = context.message
        if msg:
            task = new_task(msg)
            await event_queue.enqueue_event(task)
        else:
            raise ServerError(error=InvalidParamsError(message="Missing message."))

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(
                f"Starting assessment.\n{req.model_dump_json()}",
                context_id=context.context_id
            )
        )

        try:
            await self.agent.run_eval(req, updater)
            await updater.complete()
        except Exception as e:
            print(f"Agent error: {e}")
            await updater.failed(
                new_agent_text_message(f"Agent error: {e}", context_id=context.context_id)
            )
            raise ServerError(error=InternalError(message=str(e)))

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel is not supported.

        Raises:
            ServerError: Always raises UnsupportedOperationError
        """
        raise ServerError(error=UnsupportedOperationError())
