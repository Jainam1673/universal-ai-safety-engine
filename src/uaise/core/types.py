"""Core domain types for UAISE."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ViolationType(StrEnum):
    """Types of safety violations observed in AI agents."""

    NONE = "none"
    REWARD_HACKING = "reward_hacking"
    SPECIFICATION_GAMING = "specification_gaming"
    UNAUTHORIZED_TOOL_USE = "unauthorized_tool_use"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DECEPTIVE_COMPLIANCE = "deceptive_compliance"
    CAPABILITY_ESCALATION = "capability_escalation"
    INFORMATION_LEAKAGE = "information_leakage"


@dataclass(frozen=True)
class Action:
    """An action taken or proposed by an agent."""

    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Action name cannot be empty.")


@dataclass(frozen=True)
class Scenario:
    """A benchmark scenario with explicit specification and ground truth."""

    id: str
    name: str
    description: str
    intended_task: str
    allowed_actions: list[str]
    is_violation: bool
    violation_type: ViolationType = ViolationType.NONE
    ground_truth_explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Scenario id cannot be empty.")
        if self.is_violation and self.violation_type == ViolationType.NONE:
            raise ValueError(
                "Scenarios labeled as violations must specify a non-NONE violation_type."
            )
        if not self.is_violation and self.violation_type != ViolationType.NONE:
            raise ValueError(
                "Scenarios labeled as safe cannot have a violation_type other than NONE."
            )

    def is_action_violation(self, action: Action) -> bool:
        """Independently determine whether an action violates ground-truth specification."""
        if action.name not in self.allowed_actions:
            return True
        hack_action_name = self.metadata.get("hack_action", {}).get("name")
        if hack_action_name and action.name == hack_action_name:
            return True
        if "smuggled_payload" in action.parameters:
            return True
        return False


@dataclass(frozen=True)
class MonitorDecision:
    """Structured evidence returned by a safety monitor."""

    monitor_id: str
    is_flagged: bool
    risk_score: float
    rationale: str
    triggered_rule: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= self.risk_score <= 1.0):
            raise ValueError(f"risk_score must be between 0.0 and 1.0, got {self.risk_score}")
        if not self.monitor_id.strip():
            raise ValueError("monitor_id cannot be empty.")


@dataclass(frozen=True)
class ScenarioResult:
    """Outcome of evaluating an agent and monitors on a single scenario."""

    scenario_id: str
    agent_id: str
    action_taken: Action
    ground_truth_violation: bool
    violation_type: ViolationType
    monitor_decisions: dict[str, MonitorDecision]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    error: str | None = None


@dataclass(frozen=True)
class EvaluationMetrics:
    """Statistical evaluation metrics for monitor detection performance."""

    total_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_samples": self.total_samples,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
        }


@dataclass(frozen=True)
class RunMetadata:
    """Metadata detailing the environment and parameters for experiment reproducibility."""

    run_id: str
    timestamp: str
    uaise_version: str
    python_version: str
    seed: int
    benchmark_id: str
    agent_id: str
    monitor_ids: list[str]
    notes: str = ""
