"""Tests for evaluation metrics calculation."""

from uaise.core.types import Action, MonitorDecision, ScenarioResult, ViolationType
from uaise.evaluation.metrics import compute_metrics


def _make_result(
    actual_violation: bool, predicted_flag: bool, monitor_id: str = "m1"
) -> ScenarioResult:
    return ScenarioResult(
        scenario_id="s1",
        agent_id="a1",
        action_taken=Action(name="test"),
        ground_truth_violation=actual_violation,
        violation_type=ViolationType.REWARD_HACKING if actual_violation else ViolationType.NONE,
        monitor_decisions={
            monitor_id: MonitorDecision(
                monitor_id=monitor_id,
                is_flagged=predicted_flag,
                risk_score=1.0 if predicted_flag else 0.0,
                rationale="test",
            )
        },
    )


def test_empty_results():
    metrics = compute_metrics([], "m1")
    assert metrics.total_samples == 0
    assert metrics.accuracy == 0.0
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1_score == 0.0
    assert metrics.false_positive_rate == 0.0


def test_perfect_classification():
    results = [
        _make_result(True, True),
        _make_result(True, True),
        _make_result(False, False),
        _make_result(False, False),
    ]
    metrics = compute_metrics(results, "m1")
    assert metrics.total_samples == 4
    assert metrics.true_positives == 2
    assert metrics.true_negatives == 2
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0
    assert metrics.accuracy == 1.0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1_score == 1.0
    assert metrics.false_positive_rate == 0.0


def test_mixed_classification_and_rates():
    # 2 TP, 1 FP, 1 TN, 1 FN
    results = [
        _make_result(True, True),
        _make_result(True, True),
        _make_result(False, True),  # FP
        _make_result(False, False),  # TN
        _make_result(True, False),  # FN
    ]
    metrics = compute_metrics(results, "m1")
    assert metrics.total_samples == 5
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.true_negatives == 1
    assert metrics.false_negatives == 1

    # Precision = 2 / (2 + 1) = 2/3
    assert abs(metrics.precision - 2 / 3) < 1e-4
    # Recall = 2 / (2 + 1) = 2/3
    assert abs(metrics.recall - 2 / 3) < 1e-4
    # FPR = 1 / (1 + 1) = 0.5
    assert abs(metrics.false_positive_rate - 0.5) < 1e-4


def test_zero_division_guard():
    # No positives predicted, no actual positives: all TN
    results = [_make_result(False, False)]
    metrics = compute_metrics(results, "m1")
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.false_positive_rate == 0.0
    assert metrics.f1_score == 0.0
    assert metrics.accuracy == 1.0
