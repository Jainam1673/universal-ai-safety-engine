"""Tests for data export functions."""

from uaise.agents.scripted import ScriptedAgent
from uaise.benchmarks.toy_reward_hacking import ToyRewardHackingBenchmark
from uaise.evaluation.runner import EvaluationRunner
from uaise.monitors.action_constraint import ActionConstraintMonitor
from uaise.storage.export import (
    export_confidence_intervals_csv,
    export_correlation_matrix_csv,
    export_metrics_csv,
    export_scenario_traces_csv,
    export_threshold_curves_csv,
)


def _get_sample_run_dict():
    bench = ToyRewardHackingBenchmark()
    agent = ScriptedAgent(strategy="reward_hacker")
    monitor = ActionConstraintMonitor()
    runner = EvaluationRunner(benchmark=bench, agent=agent, monitors=[monitor], seed=42)
    return runner.run().to_dict()


def test_export_scenario_traces_csv():
    run_dict = _get_sample_run_dict()
    csv_text = export_scenario_traces_csv(run_dict)

    lines = csv_text.strip().split("\n")
    assert len(lines) == 9  # 1 header + 8 scenarios
    header = lines[0]
    assert "scenario_id" in header
    assert "ground_truth_violation" in header
    assert "flag_rule_action_constraint" in header
    assert "rh_code_opt_01" in lines[1]


def test_export_metrics_csv():
    run_dict = _get_sample_run_dict()
    csv_text = export_metrics_csv(run_dict)

    lines = csv_text.strip().split("\n")
    assert len(lines) == 2  # header + 1 monitor
    header = lines[0]
    assert "monitor_id" in header
    assert "accuracy" in header
    assert "rule_action_constraint" in lines[1]


def test_export_confidence_intervals_csv():
    run_dict = _get_sample_run_dict()
    csv_text = export_confidence_intervals_csv(run_dict)

    lines = csv_text.strip().split("\n")
    assert len(lines) > 2
    header = lines[0]
    assert "metric" in header
    assert "lower_ci_95" in header
    assert "upper_ci_95" in header


def test_export_correlation_and_thresholds_csv():
    run_dict = _get_sample_run_dict()
    corr_csv = export_correlation_matrix_csv(run_dict)
    assert "monitor_id" in corr_csv

    thresh_csv = export_threshold_curves_csv(run_dict)
    assert "true_positive_rate" in thresh_csv
    assert "threshold" in thresh_csv
