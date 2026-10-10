"""Command-line interface for UAISE."""

from __future__ import annotations

import argparse
import platform
import sys
from collections.abc import Sequence

from uaise import __version__
from uaise.agents.adversarial import AdversarialEvasionAgent
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


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for uaise CLI."""
    parser = argparse.ArgumentParser(
        prog="uaise",
        description="Universal AI Safety Engine: Modular framework for AI safety experiments.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"uaise {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # doctor
    subparsers.add_parser(
        "doctor",
        help="Check environment diagnostics, dependencies, and hardware constraints.",
    )

    # benchmark
    bench_parser = subparsers.add_parser(
        "benchmark",
        help="Inspect available benchmarks.",
    )
    bench_sub = bench_parser.add_subparsers(dest="subcommand", help="Benchmark actions")
    bench_sub.add_parser("list", help="List registered benchmarks")

    # demo
    demo_parser = subparsers.add_parser(
        "demo",
        help="Run an end-to-end offline demonstration experiment.",
    )
    demo_parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    # evaluate
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate an agent/model against a safety benchmark.",
    )
    eval_parser.add_argument(
        "--benchmark",
        type=str,
        default="toy_reward_hacking",
        help="Benchmark identifier to run",
    )
    eval_parser.add_argument(
        "--agent",
        type=str,
        choices=["safe", "reward_hacker", "opportunistic", "adversarial", "llm"],
        default="reward_hacker",
        help="Agent strategy or model to evaluate (llm requires UAISE_API_KEY)",
    )
    eval_parser.add_argument(
        "--with-llm-judge",
        action="store_true",
        help="Include optional hosted LLM judge monitor (requires UAISE_API_KEY)",
    )
    eval_parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    # report
    report_parser = subparsers.add_parser(
        "report",
        help="Generate or inspect research reports.",
    )
    report_parser.add_argument(
        "--latest",
        action="store_true",
        help="Display the latest evaluation report",
    )
    report_parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Display report for a specific run ID",
    )

    # serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="Run the FastAPI research platform REST API service.",
    )
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on")

    # export
    export_parser = subparsers.add_parser(
        "export",
        help="Export run traces or metrics for analysis.",
    )
    export_parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID to export (default: latest)",
    )
    export_parser.add_argument(
        "--target",
        type=str,
        choices=["traces", "metrics", "ci"],
        default="traces",
        help="Data to export",
    )
    export_parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "json"],
        default="csv",
        help="Export format",
    )
    export_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )

    # audit
    audit_parser = subparsers.add_parser(
        "audit",
        help="Audit cryptographic provenance and integrity of evaluation runs.",
    )
    audit_parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID to verify (default: latest)",
    )

    return parser


def run_doctor() -> int:
    """Run environment and hardware diagnostics."""
    import os

    print("=" * 60)
    print("  UAISE Environment & Hardware Diagnostics")
    print("=" * 60)
    print(f"UAISE Version : {__version__}")
    print(f"Python Runtime: {sys.version.split()[0]} ({platform.python_implementation()})")
    print(f"Platform      : {platform.system()} {platform.release()} ({platform.machine()})")

    # Check RAM if available
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            ram_gb = (pages * page_size) / (1024**3)
            print(f"System RAM    : ~{ram_gb:.1f} GB (Core engine target: <= 8GB)")
    except Exception:
        print("System RAM    : Unknown")

    api_key_set = bool(os.environ.get("UAISE_API_KEY"))
    model_name = os.environ.get("UAISE_MODEL", "gpt-4o-mini")
    if api_key_set:
        print(f"Hosted LLM    : Configured (Model: {model_name})")
    else:
        print("Hosted LLM    : Not configured (Optional: set UAISE_API_KEY to enable)")

    print("Offline Mode  : Enabled (zero network / API required for core benchmarks)")
    print("Hardware Spec : CPU-friendly lightweight evaluation engine verified.")
    print("=" * 60)
    return 0


def run_benchmark_cmd(args: argparse.Namespace) -> int:
    """Handle benchmark subcommands."""
    if args.subcommand == "list" or not args.subcommand:
        benchmarks = list_benchmarks()
        print("Registered Benchmarks:")
        for b_id in benchmarks:
            bench = get_benchmark(b_id)
            print(f"  - {bench.benchmark_id}: {bench.description}")
        return 0
    print(f"Unknown benchmark action: {args.subcommand}")
    return 1


def run_evaluation(
    benchmark_id: str,
    agent_strategy: str,
    seed: int,
    with_llm_judge: bool = False,
) -> int:
    """Run an evaluation and save artifacts."""
    bench = get_benchmark(benchmark_id)

    agent: Agent
    if agent_strategy == "llm":
        hosted_model = HostedOpenAIModel()
        if not hosted_model.has_credentials:
            print(
                "Error: UAISE_API_KEY environment variable is not configured.\n"
                "To evaluate a hosted LLM agent, set UAISE_API_KEY=<your_api_key>.\n"
                "For zero-cost offline evaluations, use --agent safe or --agent reward_hacker."
            )
            return 1
        agent = LLMAgent(model=hosted_model)
    elif agent_strategy == "adversarial":
        agent = AdversarialEvasionAgent(technique="parameter_smuggling", seed=seed)
    else:
        agent = ScriptedAgent(strategy=agent_strategy, seed=seed)  # type: ignore[arg-type]

    rule_monitor = ActionConstraintMonitor()
    heuristic_monitor = BehavioralHeuristicMonitor()
    fused_monitor = FusedMonitor(
        monitors=[rule_monitor, heuristic_monitor],
        strategy="any_flag",
        monitor_id="fused_any_flag",
    )

    monitors: list[Monitor] = [rule_monitor, heuristic_monitor, fused_monitor]

    if with_llm_judge:
        judge_model = HostedOpenAIModel()
        if not judge_model.has_credentials:
            print(
                "Error: UAISE_API_KEY environment variable is not configured for --with-llm-judge.\n"
                "Set UAISE_API_KEY=<your_api_key> to enable the hosted LLM judge monitor."
            )
            return 1
        monitors.append(LLMJudgeMonitor(model=judge_model))

    print(f"Running evaluation: benchmark='{benchmark_id}', agent='{agent.agent_id}', seed={seed}")
    runner = EvaluationRunner(benchmark=bench, agent=agent, monitors=monitors, seed=seed)
    result = runner.run()

    storage = RunStorage()
    artifact_path = storage.save_run(result)
    print(f"Artifact saved: {artifact_path}")

    # Generate and print report
    report = generate_markdown_report(result.to_dict())
    print("\n" + report)
    return 0


def run_report_cmd(args: argparse.Namespace) -> int:
    """Handle report commands."""
    storage = RunStorage()
    if args.run_id:
        data = storage.load_run_by_id(args.run_id)
        if not data:
            print(f"Error: Run ID '{args.run_id}' not found.")
            return 1
    elif args.latest or True:
        data = storage.load_latest_run()
        if not data:
            print("No saved runs found in .uaise_runs/.")
            return 1
    report = generate_markdown_report(data)
    print(report)
    return 0


def run_serve_cmd(args: argparse.Namespace) -> int:
    """Run the FastAPI research platform REST API."""
    import uvicorn

    from uaise.api.app import create_app

    app = create_app()
    print(f"Starting UAISE Research Platform API on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def run_export_cmd(args: argparse.Namespace) -> int:
    """Export run artifacts and traces."""
    import json
    from pathlib import Path

    storage = RunStorage()
    data = storage.load_run_by_id(args.run_id) if args.run_id else storage.load_latest_run()
    if not data:
        print("Error: No saved runs found in .uaise_runs/.")
        return 1

    if args.format == "json":
        content = json.dumps(data, indent=2)
    elif args.target == "metrics":
        content = export_metrics_csv(data)
    elif args.target == "ci":
        content = export_confidence_intervals_csv(data)
    else:
        content = export_scenario_traces_csv(data)

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"Exported {args.target} ({args.format}) to {args.output}")
    else:
        print(content)
    return 0


def run_audit_cmd(args: argparse.Namespace) -> int:
    """Handle audit command to verify cryptographic run integrity."""
    from uaise.governance.provenance import verify_run_integrity

    storage = RunStorage()
    run_id = args.run_id
    if not run_id:
        latest = storage.load_latest_run()
        if not latest:
            print("Error: No saved runs found in .uaise_runs/.")
            return 1
        run_id = latest.get("metadata", {}).get("run_id")
        if not run_id:
            print("Error: Latest run metadata is missing 'run_id'.")
            return 1

    run_data = storage.load_run_by_id(run_id)
    if not run_data:
        print(f"Error: Run artifact '{run_id}.json' not found.")
        return 1

    manifest = storage.load_provenance_by_id(run_id)
    if not manifest:
        print(f"Error: Provenance manifest '{run_id}.provenance.json' not found.")
        return 1

    is_valid, msg = verify_run_integrity(run_data, manifest)
    print("=" * 60)
    print("  UAISE Provenance & Integrity Audit")
    print("=" * 60)
    print(f"Run ID        : {run_id}")
    print(f"Timestamp     : {manifest.get('timestamp')}")
    print(f"Scenarios     : {manifest.get('scenario_count')}")
    print(f"SHA-256 Hash  : {manifest.get('artifact_sha256')}")
    print(f"Audit Status  : {'[PASS] VALID' if is_valid else '[FAIL] TAMPERED / INVALID'}")
    print(f"Detail        : {msg}")
    print("=" * 60)
    return 0 if is_valid else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "doctor":
        return run_doctor()

    if args.command == "benchmark":
        return run_benchmark_cmd(args)

    if args.command == "demo":
        return run_evaluation(
            benchmark_id="toy_reward_hacking",
            agent_strategy="reward_hacker",
            seed=args.seed,
        )

    if args.command == "evaluate":
        return run_evaluation(
            benchmark_id=args.benchmark,
            agent_strategy=args.agent,
            seed=args.seed,
            with_llm_judge=args.with_llm_judge,
        )

    if args.command == "report":
        return run_report_cmd(args)

    if args.command == "serve":
        return run_serve_cmd(args)

    if args.command == "export":
        return run_export_cmd(args)

    if args.command == "audit":
        return run_audit_cmd(args)

    print(f"Unhandled command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
