"""Tool management and agent communication for AgentBeats framework."""

from typing import Any
from agentbeats.client import send_message


class ToolProvider:
    """Manages agent communication and tool definitions.

    This class serves two purposes:
    1. Communication with other agents via A2A protocol
    2. Tool registration for defining available capabilities
    """

    def __init__(self):
        """Initialize tool provider with empty context and tool registry."""
        self._context_ids: dict[str, str | None] = {}
        self.tools: dict[str, dict[str, Any]] = {}

    async def talk_to_agent(self, message: str, url: str, new_conversation: bool = False) -> str:
        """Communicate with another agent by sending a message and receiving their response.

        Args:
            message: The message to send to the agent
            url: The agent's URL endpoint
            new_conversation: If True, start fresh conversation; if False, continue existing

        Returns:
            The agent's response message

        Raises:
            RuntimeError: If agent returns non-completed status
        """
        outputs = await send_message(
            message=message,
            base_url=url,
            context_id=None if new_conversation else self._context_ids.get(url, None)
        )
        if outputs.get("status", "completed") != "completed":
            raise RuntimeError(f"{url} responded with: {outputs}")
        self._context_ids[url] = outputs.get("context_id", None)
        return outputs["response"]

    def reset(self):
        """Reset conversation contexts."""
        self._context_ids = {}

    def register_tool(self, name: str, description: str, parameters: dict[str, Any]) -> None:
        """Register a tool with JSON Schema definition.

        Args:
            name: Tool name (e.g., "get_new_instance")
            description: Human-readable description
            parameters: JSON Schema parameters object
        """
        tool_def = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
        self.tools[name] = tool_def

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all registered tools in A2A format.

        Returns:
            List of tool definitions as JSON Schema compatible dicts
        """
        return list(self.tools.values())
