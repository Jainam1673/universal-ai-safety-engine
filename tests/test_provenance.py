"""Tests for cryptographic provenance and research accountability manifests."""

import copy

from uaise.governance.provenance import (
    compute_canonical_hash,
    generate_provenance_manifest,
    verify_run_integrity,
)


def test_canonical_hash_determinism():
    data1 = {"b": 2, "a": 1, "nested": {"y": [1, 2], "x": "test"}}
    data2 = {"nested": {"x": "test", "y": [1, 2]}, "a": 1, "b": 2}
    hash1 = compute_canonical_hash(data1)
    hash2 = compute_canonical_hash(data2)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_provenance_manifest_and_verification():
    run_data = {
        "metadata": {
            "run_id": "test_run_12345",
            "timestamp": "2026-10-10T00:00:00Z",
            "benchmark_id": "toy_reward_hacking",
            "agent_id": "reward_hacker",
            "seed": 42,
        },
        "scenario_results": [{"scenario_id": "s1", "is_flagged": True}],
        "summary_metrics": {"fused": {"precision": 1.0, "recall": 1.0}},
    }

    manifest = generate_provenance_manifest(run_data)
    assert manifest.run_id == "test_run_12345"
    assert manifest.scenario_count == 1
    assert len(manifest.artifact_sha256) == 64

    # Verification passes on untampered data
    is_valid, msg = verify_run_integrity(run_data, manifest.to_dict())
    assert is_valid is True
    assert "Cryptographic integrity verified" in msg

    # Verification fails on tampered data
    tampered_data = copy.deepcopy(run_data)
    tampered_data["summary_metrics"]["fused"]["recall"] = 0.5  # type: ignore[index]
    is_valid, msg = verify_run_integrity(tampered_data, manifest.to_dict())
    assert is_valid is False
    assert "Hash mismatch" in msg
