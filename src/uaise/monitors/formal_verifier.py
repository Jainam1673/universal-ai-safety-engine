"""Formal verification monitor enforcing mathematical contracts and invariants."""

from __future__ import annotations

from uaise.core.types import Action, MonitorDecision, Scenario
from uaise.formal_methods.specifications import FormalContract


class FormalVerifierMonitor:
    """Mathematical specification verifier checking agent actions against formal contracts."""

    def __init__(
        self, default_contract: FormalContract | None = None, monitor_id: str = "formal_verifier"
    ) -> None:
        self._default_contract = default_contract
        self._monitor_id = monitor_id

    @property
    def monitor_id(self) -> str:
        return self._monitor_id

    def evaluate(self, action: Action, scenario: Scenario) -> MonitorDecision:
        contract = scenario.metadata.get("formal_contract") or self._default_contract
        if contract is None:
            return MonitorDecision(
                monitor_id=self.monitor_id,
                is_flagged=False,
                risk_score=0.0,
                rationale="No formal contract specified for this scenario.",
                triggered_rule=None,
            )

        is_valid, violations = contract.verify_state_update(action.parameters)
        if not is_valid:
            return MonitorDecision(
                monitor_id=self.monitor_id,
                is_flagged=True,
                risk_score=1.0,
                rationale=f"Formal contract verification failed: {'; '.join(violations)}.",
                triggered_rule="formal_invariant_violation",
                metadata={"contract_id": contract.contract_id, "violations": violations},
            )

        return MonitorDecision(
            monitor_id=self.monitor_id,
            is_flagged=False,
            risk_score=0.0,
            rationale="Action parameters mathematically conform to formal contract invariants.",
            triggered_rule=None,
            metadata={"contract_id": contract.contract_id},
        )
