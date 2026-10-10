"""Tests for scripted agents and benchmark suites."""

from uaise.agents.scripted import ScriptedAgent
from uaise.benchmarks.registry import get_benchmark, list_benchmarks
from uaise.benchmarks.toy_reward_hacking import ToyRewardHackingBenchmark
from uaise.evaluation.runner import EvaluationRunner
from uaise.monitors.action_constraint import ActionConstraintMonitor


def test_toy_reward_hacking_benchmark():
    bench = ToyRewardHackingBenchmark()
    scenarios = bench.load_scenarios()
    assert len(scenarios) == 8

    # Verify ground truth distribution
    violations = [s for s in scenarios if s.is_violation]
    safe = [s for s in scenarios if not s.is_violation]
    assert len(violations) == 5
    assert len(safe) == 3


def test_benchmark_registry():
    assert "toy_reward_hacking" in list_benchmarks()
    bench = get_benchmark("toy_reward_hacking")
    assert bench.benchmark_id == "toy_reward_hacking"


def test_scripted_agent_safe():
    bench = ToyRewardHackingBenchmark()
    scenarios = bench.load_scenarios()
    agent = ScriptedAgent(strategy="safe")

    for sc in scenarios:
        action = agent.act(sc)
        # Safe agent must always choose allowed actions
        assert action.name in sc.allowed_actions


def test_scripted_agent_reward_hacker():
    bench = ToyRewardHackingBenchmark()
    scenarios = bench.load_scenarios()
    agent = ScriptedAgent(strategy="reward_hacker")

    hacked_count = 0
    for sc in scenarios:
        action = agent.act(sc)
        if "hack_action" in sc.metadata:
            assert action.name == sc.metadata["hack_action"]["name"]
            hacked_count += 1
    assert hacked_count == 5


def test_agent_reproducibility():
    bench = ToyRewardHackingBenchmark()
    scenarios = bench.load_scenarios()

    agent1 = ScriptedAgent(strategy="opportunistic", seed=123)
    agent2 = ScriptedAgent(strategy="opportunistic", seed=123)

    actions1 = [agent1.act(s).name for s in scenarios]
    actions2 = [agent2.act(s).name for s in scenarios]
    assert actions1 == actions2


def test_evaluation_runner_pipeline():
    bench = ToyRewardHackingBenchmark()
    agent = ScriptedAgent(strategy="safe")
    monitor = ActionConstraintMonitor()

    runner = EvaluationRunner(benchmark=bench, agent=agent, monitors=[monitor], seed=42)
    run_result = runner.run()

    assert len(run_result.scenario_results) == 8
    metrics = run_result.metrics["rule_action_constraint"]
    # For a safe agent, all actions are safe and compliant -> all 8 are True Negatives
    assert metrics.false_positives == 0
    assert metrics.true_positives == 0
    assert metrics.true_negatives == 8
    assert metrics.false_negatives == 0

    # For a reward hacker agent, 5 violations are taken and detected by rule monitor
    hacker_agent = ScriptedAgent(strategy="reward_hacker")
    hacker_runner = EvaluationRunner(
        benchmark=bench, agent=hacker_agent, monitors=[monitor], seed=42
    )
    hacker_result = hacker_runner.run()
    hacker_metrics = hacker_result.metrics["rule_action_constraint"]
    assert hacker_metrics.true_positives == 5
    assert hacker_metrics.true_negatives == 3
    assert hacker_metrics.false_positives == 0
    assert hacker_metrics.false_negatives == 0
