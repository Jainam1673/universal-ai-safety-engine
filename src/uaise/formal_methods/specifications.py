"""Formal specification representations and invariant verifiers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StateInvariant:
    """Mathematical invariant over an environment state variable."""

    variable_name: str
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: tuple[str, ...] | None = None
    description: str = ""

    def check(self, value: Any) -> tuple[bool, str]:
        """Verify if a numeric or discrete value satisfies the invariant."""
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False, f"Value {value} below minimum bound {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Value {value} exceeds maximum bound {self.max_value}"
        elif self.allowed_values is not None:
            if str(value) not in self.allowed_values:
                return False, f"Value '{value}' not in permitted discrete set {self.allowed_values}"
        return True, "Invariant satisfied"


@dataclass(frozen=True)
class FormalContract:
    """Set of formal invariants and safety specifications."""

    contract_id: str
    invariants: list[StateInvariant] = field(default_factory=list)
    description: str = ""

    def verify_state_update(self, updates: dict[str, Any]) -> tuple[bool, list[str]]:
        """Verify a proposed dictionary of state updates against all invariants."""
        violations: list[str] = []
        for inv in self.invariants:
            if inv.variable_name in updates:
                is_valid, msg = inv.check(updates[inv.variable_name])
                if not is_valid:
                    violations.append(f"{inv.variable_name}: {msg}")
        return len(violations) == 0, violations
