"""Cryptographic provenance and research accountability manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProvenanceManifest:
    """Cryptographic provenance record certifying run integrity."""

    run_id: str
    timestamp: str
    artifact_sha256: str
    scenario_count: int
    environment_summary: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "artifact_sha256": self.artifact_sha256,
            "scenario_count": self.scenario_count,
            "environment_summary": self.environment_summary,
        }


def compute_canonical_hash(data: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash over canonical JSON representation."""
    canonical_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def generate_provenance_manifest(run_data: dict[str, Any]) -> ProvenanceManifest:
    """Generate cryptographic provenance manifest for an evaluation run."""
    meta = run_data.get("metadata", {})
    run_id = meta.get("run_id", "unknown_run")
    timestamp = meta.get("timestamp", "")
    scenarios = run_data.get("scenario_results", [])

    sha256_hash = compute_canonical_hash(run_data)

    env_summary = {
        "uaise_version": meta.get("uaise_version", ""),
        "python_version": meta.get("python_version", ""),
        "seed": str(meta.get("seed", 0)),
        "benchmark_id": meta.get("benchmark_id", ""),
        "agent_id": meta.get("agent_id", ""),
    }

    return ProvenanceManifest(
        run_id=run_id,
        timestamp=timestamp,
        artifact_sha256=sha256_hash,
        scenario_count=len(scenarios),
        environment_summary=env_summary,
    )


def verify_run_integrity(run_data: dict[str, Any], manifest: dict[str, Any]) -> tuple[bool, str]:
    """Verify that evaluation run data matches the cryptographic provenance manifest."""
    expected_hash = manifest.get("artifact_sha256", "")
    if not expected_hash:
        return False, "Manifest missing 'artifact_sha256' field."

    actual_hash = compute_canonical_hash(run_data)
    if actual_hash != expected_hash:
        return (
            False,
            f"Hash mismatch: actual {actual_hash[:12]}... != expected {expected_hash[:12]}...",
        )

    return True, f"Cryptographic integrity verified (SHA-256: {actual_hash[:16]}...)"
