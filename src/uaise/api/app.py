"""FastAPI service exposing research platform endpoints for UAISE."""

from __future__ import annotations

import platform
import sys
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from uaise import __version__
from uaise.agents.base import Agent
from uaise.agents.llm_agent import LLMAgent
from uaise.agents.scripted import ScriptedAgent
from uaise.benchmarks.registry import get_benchmark, list_benchmarks
from uaise.evaluation.runner import EvaluationRunner
from uaise.models.hosted import HostedOpenAIModel
from uaise.monitors.action_constraint import ActionConstraintMonitor
from uaise.monitors.base import Monitor
from uaise.monitors.behavioral_heuristic import BehavioralHeuristicMonitor
from uaise.monitors.fusion import FusedMonitor
from uaise.monitors.llm_judge import LLMJudgeMonitor
from uaise.reporting.markdown_report import generate_markdown_report
from uaise.storage.artifact import RunStorage
from uaise.storage.export import (
    export_confidence_intervals_csv,
    export_metrics_csv,
    export_scenario_traces_csv,
)


class EvaluateRequest(BaseModel):
    benchmark_id: str = Field(default="toy_reward_hacking", description="Benchmark to evaluate")
    agent_strategy: Literal["safe", "reward_hacker", "opportunistic", "llm"] = Field(
        default="reward_hacker", description="Agent strategy or model"
    )
    seed: int = Field(default=42, description="Random seed")
    with_llm_judge: bool = Field(default=False, description="Include hosted LLM judge monitor")


def create_app() -> FastAPI:
    """Factory creating configured FastAPI instance."""
    app = FastAPI(
        title="UAISE Research Platform API",
        description="REST API for reproducible AI safety evaluation and auditable research records.",
        version=__version__,
    )
    storage = RunStorage()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "version": __version__}

    @app.get("/doctor")
    def doctor() -> dict[str, Any]:
        return {
            "uaise_version": __version__,
            "python_version": sys.version.split()[0],
            "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "offline_mode": True,
        }

    @app.get("/benchmarks")
    def list_all_benchmarks() -> list[dict[str, str]]:
        bench_ids = list_benchmarks()
        result = []
        for b_id in bench_ids:
            b = get_benchmark(b_id)
            result.append({"id": b.benchmark_id, "description": b.description})
        return result

    @app.get("/runs")
    def list_runs() -> list[dict[str, Any]]:
        runs = []
        if storage.runs_dir.exists():
            for p in sorted(storage.runs_dir.glob("run_*.json"), reverse=True):
                runs.append({"run_id": p.stem, "file": str(p)})
        return runs

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        data = storage.load_run_by_id(run_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
        return data

    @app.get("/runs/{run_id}/report")
    def get_run_report(run_id: str) -> Response:
        data = storage.load_run_by_id(run_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
        report = generate_markdown_report(data)
        return Response(content=report, media_type="text/markdown")

    @app.get("/runs/{run_id}/traces.csv")
    def get_traces_csv(run_id: str) -> Response:
        data = storage.load_run_by_id(run_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
        csv_text = export_scenario_traces_csv(data)
        return Response(content=csv_text, media_type="text/csv")

    @app.get("/runs/{run_id}/metrics.csv")
    def get_metrics_csv(run_id: str) -> Response:
        data = storage.load_run_by_id(run_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
        csv_text = export_metrics_csv(data)
        return Response(content=csv_text, media_type="text/csv")

    @app.get("/runs/{run_id}/ci.csv")
    def get_ci_csv(run_id: str) -> Response:
        data = storage.load_run_by_id(run_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
        csv_text = export_confidence_intervals_csv(data)
        return Response(content=csv_text, media_type="text/csv")

    @app.post("/runs/evaluate")
    def trigger_evaluation(req: EvaluateRequest) -> dict[str, Any]:
        try:
            bench = get_benchmark(req.benchmark_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        agent: Agent
        if req.agent_strategy == "llm":
            hosted_model = HostedOpenAIModel()
            if not hosted_model.has_credentials:
                raise HTTPException(
                    status_code=400,
                    detail="UAISE_API_KEY environment variable is not configured for LLM agent.",
                )
            agent = LLMAgent(model=hosted_model)
        else:
            agent = ScriptedAgent(strategy=req.agent_strategy, seed=req.seed)

        rule_monitor = ActionConstraintMonitor()
        heuristic_monitor = BehavioralHeuristicMonitor()
        fused_monitor = FusedMonitor(
            monitors=[rule_monitor, heuristic_monitor],
            strategy="any_flag",
            monitor_id="fused_any_flag",
        )
        monitors: list[Monitor] = [rule_monitor, heuristic_monitor, fused_monitor]

        if req.with_llm_judge:
            judge_model = HostedOpenAIModel()
            if not judge_model.has_credentials:
                raise HTTPException(
                    status_code=400,
                    detail="UAISE_API_KEY environment variable is not configured for LLM judge.",
                )
            monitors.append(LLMJudgeMonitor(model=judge_model))

        runner = EvaluationRunner(benchmark=bench, agent=agent, monitors=monitors, seed=req.seed)
        result = runner.run()
        storage.save_run(result)
        return result.to_dict()

    return app
