"""Auditing data export utilities for evaluation runs."""

from __future__ import annotations

import csv
import io
import json
from typing import Any


def export_scenario_traces_csv(run_data: dict[str, Any]) -> str:
    """Export scenario traces to a flat tabular CSV format."""
    metadata = run_data.get("metadata", {})
    run_id = metadata.get("run_id", "")
    scenarios = run_data.get("scenario_results", [])
    monitor_ids = metadata.get("monitor_ids", [])

    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    header = [
        "run_id",
        "scenario_id",
        "agent_id",
        "action_name",
        "action_parameters",
        "action_rationale",
        "ground_truth_violation",
        "violation_type",
    ]
    for m_id in monitor_ids:
        header.append(f"flag_{m_id}")
        header.append(f"risk_{m_id}")
    header.extend(["disagreement", "timestamp", "error"])
    writer.writerow(header)

    for sc in scenarios:
        action = sc.get("action_taken", {})
        decisions = sc.get("monitor_decisions", {})

        flags = [decisions.get(m, {}).get("is_flagged", False) for m in monitor_ids]
        disagreement = 0 < sum(1 for f in flags if f) < len(flags) if len(flags) > 1 else False

        row = [
            run_id,
            sc.get("scenario_id", ""),
            sc.get("agent_id", ""),
            action.get("name", ""),
            json.dumps(action.get("parameters", {})),
            action.get("rationale", ""),
            sc.get("ground_truth_violation", False),
            sc.get("violation_type", ""),
        ]

        for m_id in monitor_ids:
            m_dec = decisions.get(m_id, {})
            row.append(m_dec.get("is_flagged", False))
            row.append(m_dec.get("risk_score", 0.0))

        row.extend([disagreement, sc.get("timestamp", ""), sc.get("error", "")])
        writer.writerow(row)

    return output.getvalue()


def export_metrics_csv(run_data: dict[str, Any]) -> str:
    """Export summary metrics table to CSV format."""
    run_id = run_data.get("metadata", {}).get("run_id", "")
    metrics_map = run_data.get("metrics", {})

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "run_id",
            "monitor_id",
            "true_positives",
            "false_positives",
            "true_negatives",
            "false_negatives",
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "false_positive_rate",
        ]
    )

    for m_id, m in metrics_map.items():
        writer.writerow(
            [
                run_id,
                m_id,
                m.get("true_positives", 0),
                m.get("false_positives", 0),
                m.get("true_negatives", 0),
                m.get("false_negatives", 0),
                m.get("accuracy", 0.0),
                m.get("precision", 0.0),
                m.get("recall", 0.0),
                m.get("f1_score", 0.0),
                m.get("false_positive_rate", 0.0),
            ]
        )

    return output.getvalue()


def export_confidence_intervals_csv(run_data: dict[str, Any]) -> str:
    """Export bootstrap confidence intervals to CSV format."""
    run_id = run_data.get("metadata", {}).get("run_id", "")
    ci_map = run_data.get("confidence_intervals", {})

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "run_id",
            "monitor_id",
            "metric",
            "point_estimate",
            "lower_ci_95",
            "upper_ci_95",
            "confidence_level",
        ]
    )

    for m_id, metrics in ci_map.items():
        for metric_name, ci in metrics.items():
            writer.writerow(
                [
                    run_id,
                    m_id,
                    metric_name,
                    ci.get("point_estimate", 0.0),
                    ci.get("lower", 0.0),
                    ci.get("upper", 0.0),
                    ci.get("confidence_level", 0.95),
                ]
            )

    return output.getvalue()
