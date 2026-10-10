"""Benchmark registry."""

from __future__ import annotations

from uaise.benchmarks.base import Benchmark
from uaise.benchmarks.canary_privacy import CanaryPrivacyBenchmark
from uaise.benchmarks.cyber_physical_invariants import CyberPhysicalInvariantsBenchmark
from uaise.benchmarks.prompt_injection import PromptInjectionBenchmark
from uaise.benchmarks.toy_reward_hacking import ToyRewardHackingBenchmark

_BENCHMARKS: dict[str, type[Benchmark]] = {
    "canary_privacy": CanaryPrivacyBenchmark,
    "cyber_physical_invariants": CyberPhysicalInvariantsBenchmark,
    "prompt_injection": PromptInjectionBenchmark,
    "toy_reward_hacking": ToyRewardHackingBenchmark,
}


def get_benchmark(benchmark_id: str) -> Benchmark:
    """Retrieve an instantiated benchmark by ID."""
    if benchmark_id not in _BENCHMARKS:
        raise KeyError(
            f"Benchmark '{benchmark_id}' not found. Available benchmarks: {list_benchmarks()}"
        )
    return _BENCHMARKS[benchmark_id]()


def list_benchmarks() -> list[str]:
    """List IDs of all registered benchmarks."""
    return sorted(_BENCHMARKS.keys())
