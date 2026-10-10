"""Base agent interface."""

from __future__ import annotations

from typing import Protocol

from uaise.core.types import Action, Scenario


class Agent(Protocol):
    """Protocol for agents evaluated inside UAISE."""

    @property
    def agent_id(self) -> str:
        """Unique identifier for this agent implementation or configuration."""
        ...

    def act(self, scenario: Scenario) -> Action:
        """Choose an action given the scenario context."""
        ...
