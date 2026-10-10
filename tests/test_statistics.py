"""Tests for bootstrap confidence interval calculations."""

from uaise.core.types import Action, MonitorDecision, ScenarioResult, ViolationType
from uaise.evaluation.statistics import bootstrap_metric_ci, compute_all_bootstrap_ci


def _make_result(actual: bool, predicted: bool, monitor_id: str = "m1") -> ScenarioResult:
    return ScenarioResult(
        scenario_id="s1",
        agent_id="a1",
        action_taken=Action(name="test"),
        ground_truth_violation=actual,
        violation_type=ViolationType.REWARD_HACKING if actual else ViolationType.NONE,
        monitor_decisions={
            monitor_id: MonitorDecision(
                monitor_id=monitor_id,
                is_flagged=predicted,
                risk_score=1.0 if predicted else 0.0,
                rationale="test",
            )
        },
    )


def test_bootstrap_empty():
    ci = bootstrap_metric_ci([], "m1", "accuracy")
    assert ci.point_estimate == 0.0
    assert ci.lower == 0.0
    assert ci.upper == 0.0


def test_bootstrap_bounds_and_determinism():
    results = [
        _make_result(True, True),
        _make_result(True, True),
        _make_result(False, False),
        _make_result(False, True),  # FP
    ]
    ci1 = bootstrap_metric_ci(results, "m1", "accuracy", num_bootstrap=500, seed=42)
    ci2 = bootstrap_metric_ci(results, "m1", "accuracy", num_bootstrap=500, seed=42)

    assert ci1.point_estimate == 0.75
    assert 0.0 <= ci1.lower <= ci1.point_estimate <= ci1.upper <= 1.0
    # Determinism with fixed seed
    assert ci1.lower == ci2.lower
    assert ci1.upper == ci2.upper


def test_compute_all_bootstrap_ci():
    results = [
        _make_result(True, True),
        _make_result(False, False),
    ]
    cis = compute_all_bootstrap_ci(results, "m1", num_bootstrap=200, seed=42)
    assert "accuracy" in cis
    assert "precision" in cis
    assert "recall" in cis
    assert "f1_score" in cis
    assert "false_positive_rate" in cis

    d = cis["accuracy"].to_dict()
    assert d["confidence_level"] == 0.95
    assert d["point_estimate"] == 1.0
