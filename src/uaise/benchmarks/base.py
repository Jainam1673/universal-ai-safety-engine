"""Base benchmark interface and registry."""

from __future__ import annotations

from typing import Protocol

from uaise.core.types import Scenario


class Benchmark(Protocol):
    """Protocol for a safety benchmark suite."""

    @property
    def benchmark_id(self) -> str:
        """Unique benchmark identifier."""
        ...

    @property
    def description(self) -> str:
        """Detailed description and scientific rationale."""
        ...

    def load_scenarios(self) -> list[Scenario]:
        """Load or instantiate the scenarios belonging to this benchmark."""
        ...
