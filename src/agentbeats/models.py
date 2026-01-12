"""Core data models for AgentBeats framework."""

from typing import Any
from pydantic import BaseModel, HttpUrl


class EvalRequest(BaseModel):
    """Request to start an evaluation.

    Attributes:
        participants: Dict mapping role names to agent endpoint URLs
        config: Optional configuration parameters for the evaluation
    """
    participants: dict[str, HttpUrl]  # role -> endpoint mapping
    config: dict[str, Any]


class EvalResult(BaseModel):
    """Result of an evaluation.

    Attributes:
        winner: Role name of the winning agent (or "agent" for single-agent scenarios)
        detail: Detailed metrics and results from the evaluation
    """
    winner: str  # role of winner
    detail: dict[str, Any]
