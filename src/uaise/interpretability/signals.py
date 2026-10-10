"""Mechanistic interpretability signal definitions and entropy metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LogitEntropySignal:
    """Internal model output distribution representation for interpretability analysis."""

    logits: list[float]
    temperature: float = 1.0

    @property
    def entropy(self) -> float:
        """Compute Shannon entropy of softmax probability distribution."""
        if not self.logits:
            return 0.0

        # Stable softmax
        max_l = max(self.logits)
        exp_vals = [math.exp((x - max_l) / self.temperature) for x in self.logits]
        sum_exp = sum(exp_vals)
        if sum_exp == 0.0:
            return 0.0

        probs = [e / sum_exp for e in exp_vals]
        ent = -sum(p * math.log2(p) for p in probs if p > 0.0)
        return ent
