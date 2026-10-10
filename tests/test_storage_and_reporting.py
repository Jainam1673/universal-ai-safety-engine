"""Tests for artifact storage and report generation."""

from pathlib import Path

from uaise.agents.scripted import ScriptedAgent
from uaise.benchmarks.toy_reward_hacking import ToyRewardHackingBenchmark
from uaise.evaluation.runner import EvaluationRunner
from uaise.monitors.action_constraint import ActionConstraintMonitor
from uaise.reporting.markdown_report import generate_markdown_report
from uaise.storage.artifact import RunStorage


def test_storage_and_report_lifecycle(tmp_path: Path):
    storage = RunStorage(runs_dir=tmp_path)
    bench = ToyRewardHackingBenchmark()
    agent = ScriptedAgent(strategy="reward_hacker")
    monitor = ActionConstraintMonitor()

    runner = EvaluationRunner(benchmark=bench, agent=agent, monitors=[monitor], seed=42)
    result = runner.run()

    # Save
    saved_path = storage.save_run(result)
    assert saved_path.exists()

    # Load latest
    latest_data = storage.load_latest_run()
    assert latest_data is not None
    assert latest_data["metadata"]["run_id"] == result.metadata.run_id

    # Load by ID
    by_id_data = storage.load_run_by_id(result.metadata.run_id)
    assert by_id_data is not None
    assert by_id_data["metadata"]["run_id"] == result.metadata.run_id

    # Generate Markdown report
    report_md = generate_markdown_report(latest_data)
    assert "# UAISE Research Evaluation Report:" in report_md
    assert "Synthetic Benchmark Disclaimer" in report_md
    assert "rule_action_constraint" in report_md
