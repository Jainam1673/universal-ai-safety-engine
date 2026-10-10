"""Tests for UAISE CLI commands."""

from uaise.cli import main


def test_cli_help(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Universal AI Safety Engine" in captured.out


def test_cli_no_args(capsys):
    ret = main([])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Universal AI Safety Engine" in captured.out


def test_cli_doctor(capsys):
    ret = main(["doctor"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "UAISE Environment & Hardware Diagnostics" in captured.out
    assert "Offline Mode" in captured.out


def test_cli_benchmark_list(capsys):
    ret = main(["benchmark", "list"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "toy_reward_hacking" in captured.out


def test_cli_demo(capsys):
    ret = main(["demo", "--seed", "42"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Artifact saved:" in captured.out
    assert "UAISE Research Evaluation Report:" in captured.out


def test_cli_report_latest(capsys):
    # After demo runs, latest report should exist
    ret = main(["report", "--latest"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "UAISE Research Evaluation Report:" in captured.out


def test_cli_evaluate_llm_without_key(capsys, monkeypatch):
    monkeypatch.delenv("UAISE_API_KEY", raising=False)
    ret = main(["evaluate", "--agent", "llm"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error: UAISE_API_KEY environment variable is not configured" in captured.out


def test_cli_evaluate_with_llm_judge_without_key(capsys, monkeypatch):
    monkeypatch.delenv("UAISE_API_KEY", raising=False)
    ret = main(["evaluate", "--agent", "safe", "--with-llm-judge"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error: UAISE_API_KEY environment variable is not configured" in captured.out


def test_cli_evaluate_adversarial(capsys):
    ret = main(["evaluate", "--agent", "adversarial"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "adversarial_agent_parameter_smuggling" in captured.out


def test_cli_export_traces(capsys):
    ret = main(["export", "--target", "traces", "--format", "csv"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "scenario_id" in captured.out
    assert "ground_truth_violation" in captured.out


def test_cli_audit(capsys):
    # After demo runs, audit should verify the latest run
    ret = main(["audit"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "UAISE Provenance & Integrity Audit" in captured.out
    assert "[PASS] VALID" in captured.out
    assert "Cryptographic integrity verified" in captured.out
