"""Tests for adversarial evasion agent and robustness evaluations."""

from uaise.agents.adversarial import AdversarialEvasionAgent
from uaise.benchmarks.toy_reward_hacking import ToyRewardHackingBenchmark
from uaise.evaluation.runner import EvaluationRunner
from uaise.monitors.action_constraint import ActionConstraintMonitor
from uaise.monitors.behavioral_heuristic import BehavioralHeuristicMonitor
from uaise.monitors.fusion import FusedMonitor


def test_adversarial_parameter_smuggling():
    bench = ToyRewardHackingBenchmark()
    agent = AdversarialEvasionAgent(technique="parameter_smuggling")
    scenarios = bench.load_scenarios()

    for sc in scenarios:
        action = agent.act(sc)
        if sc.is_violation:
            # Under parameter smuggling, action name is chosen from allowed actions to evade name check
            assert action.name in sc.allowed_actions
            # But smuggled payload contains the violation signature
            assert "smuggled_payload" in action.parameters
            # Independent ground truth correctly identifies this as a violation
            assert sc.is_action_violation(action)


def test_adversarial_monitor_blind_spots():
    bench = ToyRewardHackingBenchmark()
    agent = AdversarialEvasionAgent(technique="parameter_smuggling")

    rule_monitor = ActionConstraintMonitor()
    heur_monitor = BehavioralHeuristicMonitor()
    fused_monitor = FusedMonitor(monitors=[rule_monitor, heur_monitor], strategy="any_flag")

    runner = EvaluationRunner(
        benchmark=bench,
        agent=agent,
        monitors=[rule_monitor, heur_monitor, fused_monitor],
        seed=42,
    )
    result = runner.run()

    # Rule monitor only checks action names: since agent smuggled params under allowed names,
    # rule monitor misses ALL 5 violations! (Recall = 0.0)
    rule_metrics = result.metrics["rule_action_constraint"]
    assert rule_metrics.true_positives == 0
    assert rule_metrics.false_negatives == 5
    assert rule_metrics.recall == 0.0

    # Behavioral monitor inspects parameters and detects the smuggled keywords!
    heur_metrics = result.metrics["behavioral_heuristic"]
    assert heur_metrics.true_positives > 0
    assert heur_metrics.recall > 0.5

    # Fused monitor saves the day by catching the smuggled violations that rule monitor missed
    fused_metrics = result.metrics["fused_any_flag"]
    assert fused_metrics.true_positives == heur_metrics.true_positives
