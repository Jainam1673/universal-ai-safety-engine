"""Statistical analysis and uncertainty estimation via bootstrap confidence intervals."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from uaise.core.types import ScenarioResult
from uaise.evaluation.metrics import compute_metrics


@dataclass(frozen=True)
class ConfidenceInterval:
    """Non-parametric empirical confidence interval."""

    point_estimate: float
    lower: float
    upper: float
    confidence_level: float = 0.95

    def to_dict(self) -> dict[str, Any]:
        return {
            "point_estimate": round(self.point_estimate, 4),
            "lower": round(self.lower, 4),
            "upper": round(self.upper, 4),
            "confidence_level": self.confidence_level,
        }


def bootstrap_metric_ci(
    results: list[ScenarioResult],
    monitor_id: str,
    metric_name: str,
    num_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> ConfidenceInterval:
    """Compute empirical percentile bootstrap confidence interval for a metric.

    Resamples scenario results with replacement.
    """
    if not results:
        return ConfidenceInterval(0.0, 0.0, 0.0, confidence_level)

    base_metrics = compute_metrics(results, monitor_id)
    point_est = getattr(base_metrics, metric_name, 0.0)

    rng = random.Random(seed)
    n = len(results)
    bootstrap_estimates: list[float] = []

    for _ in range(num_bootstrap):
        sample = [results[rng.randrange(n)] for _ in range(n)]
        sample_metric = getattr(compute_metrics(sample, monitor_id), metric_name, 0.0)
        bootstrap_estimates.append(sample_metric)

    bootstrap_estimates.sort()
    alpha = (1.0 - confidence_level) / 2.0
    lower_idx = int(alpha * num_bootstrap)
    upper_idx = int((1.0 - alpha) * num_bootstrap) - 1
    lower_idx = max(0, min(num_bootstrap - 1, lower_idx))
    upper_idx = max(0, min(num_bootstrap - 1, upper_idx))

    return ConfidenceInterval(
        point_estimate=point_est,
        lower=bootstrap_estimates[lower_idx],
        upper=bootstrap_estimates[upper_idx],
        confidence_level=confidence_level,
    )


def compute_all_bootstrap_ci(
    results: list[ScenarioResult],
    monitor_id: str,
    num_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> dict[str, ConfidenceInterval]:
    """Calculate 95% bootstrap confidence intervals for all primary metrics."""
    metrics_to_compute = ["accuracy", "precision", "recall", "f1_score", "false_positive_rate"]
    ci_map: dict[str, ConfidenceInterval] = {}
    for metric_name in metrics_to_compute:
        ci_map[metric_name] = bootstrap_metric_ci(
            results,
            monitor_id,
            metric_name,
            num_bootstrap=num_bootstrap,
            confidence_level=confidence_level,
            seed=seed,
        )
    return ci_map
