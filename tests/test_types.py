"""Tests for core domain types and validations."""

import pytest

from uaise.core.types import Action, MonitorDecision, Scenario, ViolationType


def test_action_validation():
    action = Action(name="read_file", parameters={"path": "test.txt"}, rationale="test")
    assert action.name == "read_file"
    assert action.parameters["path"] == "test.txt"

    with pytest.raises(ValueError, match="Action name cannot be empty"):
        Action(name="   ")


def test_scenario_validation():
    # Valid safe scenario
    sc = Scenario(
        id="sc_01",
        name="Safe Operation",
        description="A safe task",
        intended_task="Do safe task",
        allowed_actions=["do_safe"],
        is_violation=False,
        violation_type=ViolationType.NONE,
    )
    assert sc.id == "sc_01"
    assert not sc.is_violation

    # Violation scenario without violation type should raise
    with pytest.raises(ValueError, match="Scenarios labeled as violations must specify"):
        Scenario(
            id="sc_02",
            name="Violation Task",
            description="desc",
            intended_task="task",
            allowed_actions=["act"],
            is_violation=True,
            violation_type=ViolationType.NONE,
        )

    # Safe scenario with violation type should raise
    with pytest.raises(ValueError, match="Scenarios labeled as safe cannot have a violation_type"):
        Scenario(
            id="sc_03",
            name="Confused Task",
            description="desc",
            intended_task="task",
            allowed_actions=["act"],
            is_violation=False,
            violation_type=ViolationType.REWARD_HACKING,
        )


def test_monitor_decision_validation():
    dec = MonitorDecision(
        monitor_id="m1",
        is_flagged=True,
        risk_score=0.85,
        rationale="Looks suspicious",
    )
    assert dec.is_flagged
    assert dec.risk_score == 0.85

    with pytest.raises(ValueError, match="risk_score must be between 0.0 and 1.0"):
        MonitorDecision(monitor_id="m1", is_flagged=True, risk_score=1.5, rationale="")

    with pytest.raises(ValueError, match="risk_score must be between 0.0 and 1.0"):
        MonitorDecision(monitor_id="m1", is_flagged=False, risk_score=-0.1, rationale="")
