"""Synthetic canary tracking for privacy and information leakage evaluation."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticCanary:
    """A synthetic secret token injected into scenario context to audit data leakage."""

    canary_id: str
    token: str
    description: str = ""


class CanaryTracker:
    """Scans text and data structures for confidential synthetic canaries."""

    def __init__(self, canaries: list[SyntheticCanary] | None = None) -> None:
        self.canaries = list(canaries) if canaries else []

    def scan_text(self, text: str) -> list[SyntheticCanary]:
        """Return list of canaries found within raw text."""
        leaked = []
        for c in self.canaries:
            # Word boundary search or literal containment
            if re.search(re.escape(c.token), text, re.IGNORECASE):
                leaked.append(c)
        return leaked
