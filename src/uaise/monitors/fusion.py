"""Evidence fusion mechanisms combining multiple safety monitors."""

from __future__ import annotations

from typing import Literal

from uaise.core.types import Action, MonitorDecision, Scenario
from uaise.monitors.base import Monitor

FusionStrategy = Literal["any_flag", "all_flag", "weighted_average"]


class FusedMonitor:
    """Combines evidence from multiple independent safety monitors.

    Maintains individual decisions and transparent aggregation rules.
    """

    def __init__(
        self,
        monitors: list[Monitor],
        strategy: FusionStrategy = "any_flag",
        weights: dict[str, float] | None = None,
        threshold: float = 0.5,
        monitor_id: str | None = None,
    ) -> None:
        if not monitors:
            raise ValueError("FusedMonitor requires at least one monitor.")
        self.monitors = monitors
        self.strategy = strategy
        self.threshold = threshold
        self.weights = weights or {m.monitor_id: 1.0 / len(monitors) for m in monitors}
        self._monitor_id = monitor_id or f"fused_{strategy}"

    @property
    def monitor_id(self) -> str:
        return self._monitor_id

    def evaluate(self, action: Action, scenario: Scenario) -> MonitorDecision:
        individual_decisions: dict[str, MonitorDecision] = {}
        for m in self.monitors:
            decision = m.evaluate(action, scenario)
            individual_decisions[m.monitor_id] = decision

        if self.strategy == "any_flag":
            flagged = any(d.is_flagged for d in individual_decisions.values())
            risk_score = max(d.risk_score for d in individual_decisions.values())
            rationale = (
                f"Flagged by at least one monitor (any_flag strategy). "
                f"Contributing flags: {[m_id for m_id, d in individual_decisions.items() if d.is_flagged]}"
                if flagged
                else "No monitor flagged this action."
            )
        elif self.strategy == "all_flag":
            flagged = all(d.is_flagged for d in individual_decisions.values())
            risk_score = min(d.risk_score for d in individual_decisions.values())
            rationale = (
                "Unanimously flagged by all monitors (all_flag consensus)."
                if flagged
                else "Action was not flagged unanimously by all monitors."
            )
        elif self.strategy == "weighted_average":
            total_weight = sum(self.weights.get(m_id, 1.0) for m_id in individual_decisions)
            risk_score = (
                sum(
                    d.risk_score * self.weights.get(m_id, 1.0)
                    for m_id, d in individual_decisions.items()
                )
                / total_weight
                if total_weight > 0
                else 0.0
            )
            flagged = risk_score >= self.threshold
            rationale = (
                f"Weighted risk score {risk_score:.3f} >= threshold {self.threshold:.3f}"
                if flagged
                else f"Weighted risk score {risk_score:.3f} < threshold {self.threshold:.3f}"
            )
        else:
            raise ValueError(f"Unknown fusion strategy: {self.strategy}")

        return MonitorDecision(
            monitor_id=self.monitor_id,
            is_flagged=flagged,
            risk_score=risk_score,
            rationale=rationale,
            triggered_rule=f"fusion_{self.strategy}" if flagged else None,
            metadata={
                "strategy": self.strategy,
                "individual_decisions": {
                    k: {
                        "is_flagged": v.is_flagged,
                        "risk_score": v.risk_score,
                        "triggered_rule": v.triggered_rule,
                    }
                    for k, v in individual_decisions.items()
                },
            },
        )
