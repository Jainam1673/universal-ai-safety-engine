"""Monitor correlation and pairwise disagreement analysis."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def compute_phi_coefficient(flags_a: Sequence[bool], flags_b: Sequence[bool]) -> float:
    """Compute the Pearson phi correlation coefficient between two binary decision vectors."""
    if len(flags_a) != len(flags_b):
        raise ValueError("Decision sequences must have identical lengths.")
    n = len(flags_a)
    if n == 0:
        return 0.0

    n11 = sum(1 for a, b in zip(flags_a, flags_b, strict=True) if a and b)
    n10 = sum(1 for a, b in zip(flags_a, flags_b, strict=True) if a and not b)
    n01 = sum(1 for a, b in zip(flags_a, flags_b, strict=True) if not a and b)
    n00 = sum(1 for a, b in zip(flags_a, flags_b, strict=True) if not a and not b)

    n1_ = n11 + n10
    n0_ = n01 + n00
    n_1 = n11 + n01
    n_0 = n10 + n00

    denom = math.sqrt(n1_ * n0_ * n_1 * n_0)
    if denom == 0.0:
        # If both series are completely identical constants, phi is 1.0; otherwise uncorrelated (0.0)
        return 1.0 if flags_a == flags_b else 0.0

    return (n11 * n00 - n10 * n01) / denom


def compute_disagreement_rate(flags_a: Sequence[bool], flags_b: Sequence[bool]) -> float:
    """Compute proportion of cases where two monitors disagree."""
    if len(flags_a) != len(flags_b):
        raise ValueError("Decision sequences must have identical lengths.")
    if not flags_a:
        return 0.0
    disagreements = sum(1 for a, b in zip(flags_a, flags_b, strict=True) if a != b)
    return disagreements / len(flags_a)


def compute_monitor_correlation_matrix(
    decisions_by_monitor: Mapping[str, Sequence[bool]],
) -> dict[str, dict[str, float]]:
    """Compute pairwise phi correlation matrix across all monitors."""
    matrix: dict[str, dict[str, float]] = {}
    monitor_ids = list(decisions_by_monitor.keys())

    for m_a in monitor_ids:
        matrix[m_a] = {}
        for m_b in monitor_ids:
            if m_a == m_b:
                matrix[m_a][m_b] = 1.0
            else:
                matrix[m_a][m_b] = round(
                    compute_phi_coefficient(decisions_by_monitor[m_a], decisions_by_monitor[m_b]), 4
                )

    return matrix
