"""Continuous risk score threshold sweeping, ROC curves, and Precision-Recall analysis."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionCurvePoint:
    """Evaluation metrics at a specific decision risk threshold."""

    threshold: float
    true_positive_rate: float
    false_positive_rate: float
    precision: float
    recall: float
    f1_score: float

    def to_dict(self) -> dict[str, float]:
        return {
            "threshold": self.threshold,
            "true_positive_rate": self.true_positive_rate,
            "false_positive_rate": self.false_positive_rate,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
        }


@dataclass(frozen=True)
class ThresholdCurve:
    """Parametric decision threshold curve and area-under-curve metrics."""

    points: list[DecisionCurvePoint]
    auc_roc: float
    auc_pr: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "auc_roc": self.auc_roc,
            "auc_pr": self.auc_pr,
            "points": [p.to_dict() for p in self.points],
        }


def _trapezoid_auc(x_vals: list[float], y_vals: list[float]) -> float:
    """Compute Area Under Curve using trapezoidal integration for sorted x."""
    if len(x_vals) < 2:
        return 0.0
    auc = 0.0
    for i in range(len(x_vals) - 1):
        dx = x_vals[i + 1] - x_vals[i]
        avg_y = (y_vals[i] + y_vals[i + 1]) / 2.0
        auc += dx * avg_y
    return max(0.0, min(1.0, auc))


def sweep_decision_thresholds(
    risk_scores: Sequence[float],
    ground_truths: Sequence[bool],
    step: float = 0.05,
) -> ThresholdCurve:
    """Evaluate performance across risk threshold values from 0.0 to 1.0."""
    if len(risk_scores) != len(ground_truths):
        raise ValueError("risk_scores and ground_truths must have equal lengths.")

    n_pos = sum(1 for gt in ground_truths if gt)
    n_neg = sum(1 for gt in ground_truths if not gt)

    points: list[DecisionCurvePoint] = []
    threshold = 0.0

    # Ensure step does not produce infinite loops
    step = max(0.01, min(0.5, step))

    while threshold <= 1.0001:
        th = round(threshold, 4)
        flags = [score >= th for score in risk_scores]

        tp = sum(1 for f, gt in zip(flags, ground_truths, strict=True) if f and gt)
        fp = sum(1 for f, gt in zip(flags, ground_truths, strict=True) if f and not gt)

        tpr = tp / n_pos if n_pos > 0 else 0.0
        fpr = fp / n_neg if n_neg > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tpr
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        points.append(
            DecisionCurvePoint(
                threshold=th,
                true_positive_rate=round(tpr, 4),
                false_positive_rate=round(fpr, 4),
                precision=round(prec, 4),
                recall=round(rec, 4),
                f1_score=round(f1, 4),
            )
        )
        threshold += step

    # Compute AUC-ROC (sorted by FPR ascending)
    # Add boundary endpoints (0,0) and (1,1) if not present
    roc_pairs = sorted(
        [(p.false_positive_rate, p.true_positive_rate) for p in points], key=lambda x: (x[0], x[1])
    )
    unique_roc: list[tuple[float, float]] = []
    for fpr_val, tpr_val in roc_pairs:
        if not unique_roc or unique_roc[-1][0] != fpr_val:
            unique_roc.append((fpr_val, tpr_val))
        else:
            # Keep highest TPR for duplicate FPR
            unique_roc[-1] = (fpr_val, max(unique_roc[-1][1], tpr_val))

    if unique_roc[0][0] > 0.0:
        unique_roc.insert(0, (0.0, 0.0))
    if unique_roc[-1][0] < 1.0:
        unique_roc.append((1.0, 1.0))

    auc_roc = _trapezoid_auc([p[0] for p in unique_roc], [p[1] for p in unique_roc])

    # Compute AUC-PR (Recall vs Precision)
    pr_pairs = sorted([(p.recall, p.precision) for p in points], key=lambda x: x[0])
    unique_pr: list[tuple[float, float]] = []
    for rec_val, prec_val in pr_pairs:
        if not unique_pr or unique_pr[-1][0] != rec_val:
            unique_pr.append((rec_val, prec_val))
        else:
            unique_pr[-1] = (rec_val, max(unique_pr[-1][1], prec_val))

    auc_pr = _trapezoid_auc([p[0] for p in unique_pr], [p[1] for p in unique_pr])

    return ThresholdCurve(
        points=points,
        auc_roc=round(auc_roc, 4),
        auc_pr=round(auc_pr, 4),
    )
