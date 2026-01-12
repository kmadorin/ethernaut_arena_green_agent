"""Ethernaut Arena Green Agent Server - A2A entry point."""

import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from agentbeats.green_executor import GreenExecutor
from ethernaut.evaluator import EthernautEvaluator, ethernaut_evaluator_agent_card


def main():
    parser = argparse.ArgumentParser(description="Run the Ethernaut Arena Green Agent.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9009, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="URL to advertise in the agent card")
    args = parser.parse_args()

    # Create agent card for the Ethernaut evaluator
    agent_card = ethernaut_evaluator_agent_card(
        name="Ethernaut Evaluator",
        url=args.card_url or f"http://{args.host}:{args.port}/"
    )

    # Create the evaluator and wrap it in GreenExecutor
    evaluator = EthernautEvaluator()
    request_handler = DefaultRequestHandler(
        agent_executor=GreenExecutor(evaluator),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    uvicorn.run(server.build(), host=args.host, port=args.port)


if __name__ == '__main__':
    main()
