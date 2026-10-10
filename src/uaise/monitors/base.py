"""Base monitor interface."""

from __future__ import annotations

from typing import Protocol

from uaise.core.types import Action, MonitorDecision, Scenario


class Monitor(Protocol):
    """Protocol for safety monitors evaluating agent actions within scenarios."""

    @property
    def monitor_id(self) -> str:
        """Unique monitor identifier."""
        ...

    def evaluate(self, action: Action, scenario: Scenario) -> MonitorDecision:
        """Evaluate an action within a scenario and return structured evidence."""
        ...
