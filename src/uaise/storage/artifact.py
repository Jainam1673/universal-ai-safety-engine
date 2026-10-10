"""Storage and persistence for evaluation run artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uaise.evaluation.runner import EvaluationRunResult
from uaise.governance.provenance import generate_provenance_manifest

DEFAULT_RUNS_DIR = Path(".uaise_runs")


class RunStorage:
    """Stores and retrieves evaluation runs as structured JSON artifacts."""

    def __init__(self, runs_dir: Path | str = DEFAULT_RUNS_DIR) -> None:
        self.runs_dir = Path(runs_dir)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def save_run(self, run_result: EvaluationRunResult) -> Path:
        """Persist evaluation run result as a JSON artifact."""
        filename = f"{run_result.metadata.run_id}.json"
        target_path = self.runs_dir / filename
        data = run_result.to_dict()
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Generate and save cryptographic provenance manifest
        manifest = generate_provenance_manifest(data)
        prov_path = self.runs_dir / f"{run_result.metadata.run_id}.provenance.json"
        with open(prov_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)

        # Maintain a pointer to latest run
        latest_path = self.runs_dir / "latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(
                {"latest_run_id": run_result.metadata.run_id, "file": str(target_path)}, f, indent=2
            )

        return target_path

    def load_provenance_by_id(self, run_id: str) -> dict[str, Any] | None:
        """Load cryptographic provenance manifest for a run."""
        prov_path = self.runs_dir / f"{run_id}.provenance.json"
        if not prov_path.exists():
            return None
        with open(prov_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data

    def load_latest_run(self) -> dict[str, Any] | None:
        """Load the most recent evaluation run data."""
        latest_ptr = self.runs_dir / "latest.json"
        if not latest_ptr.exists():
            return None
        with open(latest_ptr, encoding="utf-8") as f:
            ptr_data = json.load(f)
        run_file = Path(ptr_data["file"])
        if not run_file.exists():
            return None
        with open(run_file, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data

    def load_run_by_id(self, run_id: str) -> dict[str, Any] | None:
        """Load a specific evaluation run by ID."""
        run_file = self.runs_dir / f"{run_id}.json"
        if not run_file.exists():
            return None
        with open(run_file, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data
