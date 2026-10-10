"""Evaluation runner orchestrating agents, benchmarks, and monitors."""

from __future__ import annotations

import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uaise import __version__
from uaise.agents.base import Agent
from uaise.benchmarks.base import Benchmark
from uaise.core.types import Action, EvaluationMetrics, RunMetadata, ScenarioResult, ViolationType
from uaise.evaluation.correlation import compute_monitor_correlation_matrix
from uaise.evaluation.metrics import compute_metrics
from uaise.evaluation.statistics import ConfidenceInterval, compute_all_bootstrap_ci
from uaise.evaluation.thresholds import ThresholdCurve, sweep_decision_thresholds
from uaise.monitors.base import Monitor


@dataclass(frozen=True)
class EvaluationRunResult:
    """Complete result of an evaluation run including per-scenario traces and metrics."""

    metadata: RunMetadata
    scenario_results: list[ScenarioResult]
    metrics: dict[str, EvaluationMetrics]
    confidence_intervals: dict[str, dict[str, ConfidenceInterval]] = field(default_factory=dict)
    correlation_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
    threshold_curves: dict[str, ThresholdCurve] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": {
                "run_id": self.metadata.run_id,
                "timestamp": self.metadata.timestamp,
                "uaise_version": self.metadata.uaise_version,
                "python_version": self.metadata.python_version,
                "seed": self.metadata.seed,
                "benchmark_id": self.metadata.benchmark_id,
                "agent_id": self.metadata.agent_id,
                "monitor_ids": self.metadata.monitor_ids,
                "notes": self.metadata.notes,
            },
            "scenario_results": [
                {
                    "scenario_id": r.scenario_id,
                    "agent_id": r.agent_id,
                    "action_taken": {
                        "name": r.action_taken.name,
                        "parameters": r.action_taken.parameters,
                        "rationale": r.action_taken.rationale,
                    },
                    "ground_truth_violation": r.ground_truth_violation,
                    "violation_type": r.violation_type.value,
                    "monitor_decisions": {
                        k: {
                            "monitor_id": v.monitor_id,
                            "is_flagged": v.is_flagged,
                            "risk_score": v.risk_score,
                            "rationale": v.rationale,
                            "triggered_rule": v.triggered_rule,
                        }
                        for k, v in r.monitor_decisions.items()
                    },
                    "timestamp": r.timestamp,
                    "error": r.error,
                }
                for r in self.scenario_results
            ],
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "confidence_intervals": {
                m_id: {k: v.to_dict() for k, v in ci_dict.items()}
                for m_id, ci_dict in self.confidence_intervals.items()
            },
            "correlation_matrix": self.correlation_matrix,
            "threshold_curves": {
                m_id: curve.to_dict() for m_id, curve in self.threshold_curves.items()
            },
        }


class EvaluationRunner:
    """Executes benchmarks against agents and evaluates monitors."""

    def __init__(
        self, benchmark: Benchmark, agent: Agent, monitors: Sequence[Monitor], seed: int = 42
    ) -> None:
        self.benchmark = benchmark
        self.agent = agent
        self.monitors = list(monitors)
        self.seed = seed

    def run(self) -> EvaluationRunResult:
        run_id = f"run_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        scenarios = self.benchmark.load_scenarios()
        results: list[ScenarioResult] = []

        for scenario in scenarios:
            try:
                action = self.agent.act(scenario)
                is_violation = scenario.is_action_violation(action)
                v_type = scenario.violation_type if is_violation else ViolationType.NONE

                decisions = {}
                for monitor in self.monitors:
                    decision = monitor.evaluate(action, scenario)
                    decisions[monitor.monitor_id] = decision

                results.append(
                    ScenarioResult(
                        scenario_id=scenario.id,
                        agent_id=self.agent.agent_id,
                        action_taken=action,
                        ground_truth_violation=is_violation,
                        violation_type=v_type,
                        monitor_decisions=decisions,
                    )
                )
            except Exception as e:
                # Capture error without aborting run, isolating failure boundaries
                results.append(
                    ScenarioResult(
                        scenario_id=scenario.id,
                        agent_id=self.agent.agent_id,
                        action_taken=Action(name="execution_error", rationale=str(e)),
                        ground_truth_violation=scenario.is_violation,
                        violation_type=scenario.violation_type
                        if scenario.is_violation
                        else ViolationType.NONE,
                        monitor_decisions={},
                        error=f"Execution error on scenario {scenario.id}: {e}",
                    )
                )

        metrics: dict[str, EvaluationMetrics] = {}
        confidence_intervals: dict[str, dict[str, ConfidenceInterval]] = {}
        for monitor in self.monitors:
            metrics[monitor.monitor_id] = compute_metrics(results, monitor.monitor_id)
            confidence_intervals[monitor.monitor_id] = compute_all_bootstrap_ci(
                results,
                monitor.monitor_id,
                num_bootstrap=1000,
                confidence_level=0.95,
                seed=self.seed,
            )

        # Compute monitor correlation matrix
        decisions_by_monitor: dict[str, list[bool]] = {}
        for monitor in self.monitors:
            decisions_by_monitor[monitor.monitor_id] = [
                r.monitor_decisions[monitor.monitor_id].is_flagged
                for r in results
                if monitor.monitor_id in r.monitor_decisions
            ]
        correlation_matrix = compute_monitor_correlation_matrix(decisions_by_monitor)

        # Compute threshold curves (ROC and PR)
        threshold_curves: dict[str, ThresholdCurve] = {}
        ground_truths = [r.ground_truth_violation for r in results]
        for monitor in self.monitors:
            scores = [
                r.monitor_decisions[monitor.monitor_id].risk_score
                for r in results
                if monitor.monitor_id in r.monitor_decisions
            ]
            if len(scores) == len(ground_truths) and len(scores) > 0:
                threshold_curves[monitor.monitor_id] = sweep_decision_thresholds(
                    scores, ground_truths
                )

        metadata = RunMetadata(
            run_id=run_id,
            timestamp=datetime.now(UTC).isoformat(),
            uaise_version=__version__,
            python_version=sys.version.split()[0],
            seed=self.seed,
            benchmark_id=self.benchmark.benchmark_id,
            agent_id=self.agent.agent_id,
            monitor_ids=[m.monitor_id for m in self.monitors],
            notes="Deterministic benchmark evaluation run",
        )

        return EvaluationRunResult(
            metadata=metadata,
            scenario_results=results,
            metrics=metrics,
            confidence_intervals=confidence_intervals,
            correlation_matrix=correlation_matrix,
            threshold_curves=threshold_curves,
        )
