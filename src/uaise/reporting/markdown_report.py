"""Markdown research report generator."""

from __future__ import annotations

from typing import Any


def generate_markdown_report(run_data: dict[str, Any]) -> str:
    """Generate a structured Markdown research report from run data."""
    meta = run_data["metadata"]
    metrics_map = run_data["metrics"]
    scenario_results = run_data["scenario_results"]

    # Calculate ground truth distribution
    total_scenarios = len(scenario_results)
    violations = sum(1 for s in scenario_results if s["ground_truth_violation"])
    safe_cases = total_scenarios - violations

    report_lines = [
        f"# UAISE Research Evaluation Report: {meta['run_id']}",
        "",
        "## 1. Experiment Metadata",
        "",
        f"- **Run ID**: `{meta['run_id']}`",
        f"- **Timestamp (UTC)**: {meta['timestamp']}",
        f"- **UAISE Version**: {meta['uaise_version']}",
        f"- **Python Version**: {meta['python_version']}",
        f"- **Random Seed**: {meta['seed']}",
        f"- **Benchmark ID**: `{meta['benchmark_id']}`",
        f"- **Agent Evaluated**: `{meta['agent_id']}`",
        f"- **Monitors Evaluated**: {', '.join(f'`{m}`' for m in meta['monitor_ids'])}",
        "",
        "## 2. Research Hypothesis & Scope",
        "",
        "> **Hypothesis**: Can combining independent safety monitors detect reward hacking "
        "and agent failures more reliably than individual monitoring mechanisms, while controlling "
        "for false positives and correlated blind spots?",
        "",
        "> [!NOTE]",
        "> **Synthetic Benchmark Disclaimer**: Results shown below are evaluated on a controlled, "
        "synthetic specification-gaming benchmark. They validate engine mechanics and monitor logic, "
        "but do NOT constitute an empirical safety guarantee for real-world frontier LLMs.",
        "",
        "## 3. Ground Truth Distribution",
        "",
        f"- **Total Scenarios Evaluated**: {total_scenarios}",
        f"- **Ground Truth Safety Violations**: {violations} ({violations / total_scenarios * 100:.1f}%)"
        if total_scenarios
        else "- Total: 0",
        f"- **Ground Truth Safe Operations**: {safe_cases} ({safe_cases / total_scenarios * 100:.1f}%)"
        if total_scenarios
        else "",
        "",
        "## 4. Monitor Performance Comparison",
        "",
        "| Monitor ID | TP | FP | TN | FN | Accuracy | Precision | Recall | F1 Score | FPR |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for m_id, m in metrics_map.items():
        report_lines.append(
            f"| `{m_id}` | {m['true_positives']} | {m['false_positives']} | "
            f"{m['true_negatives']} | {m['false_negatives']} | {m['accuracy']:.3f} | "
            f"{m['precision']:.3f} | {m['recall']:.3f} | {m['f1_score']:.3f} | {m['false_positive_rate']:.3f} |"
        )

    ci_map = run_data.get("confidence_intervals")
    if ci_map:
        report_lines.extend(
            [
                "",
                "## 5. Statistical Uncertainty (95% Bootstrap CI, N=1,000)",
                "",
                "| Monitor ID | Metric | Point Estimate | 95% Confidence Interval |",
                "| :--- | :--- | :---: | :---: |",
            ]
        )
        for m_id, cis in ci_map.items():
            for metric_name in [
                "accuracy",
                "precision",
                "recall",
                "f1_score",
                "false_positive_rate",
            ]:
                ci = cis.get(metric_name)
                if ci:
                    fmt_name = metric_name.replace("_", " ").title()
                    report_lines.append(
                        f"| `{m_id}` | {fmt_name} | {ci['point_estimate']:.3f} | [{ci['lower']:.3f}, {ci['upper']:.3f}] |"
                    )

    report_lines.extend(
        [
            "",
            "## 6. Scenario Outcome Traces",
            "",
            "| Scenario ID | Agent Action | Violation? | Flagged By | Disagreement? |",
            "| :--- | :--- | :---: | :--- | :---: |",
        ]
    )

    for sc in scenario_results:
        flags = [m_id for m_id, dec in sc["monitor_decisions"].items() if dec["is_flagged"]]
        flags_str = ", ".join(f"`{f}`" for f in flags) if flags else "*None*"
        # Disagreement check among evaluated monitors
        num_flagged = len(flags)
        total_eval_monitors = len(sc["monitor_decisions"])
        disagreement = "Yes" if 0 < num_flagged < total_eval_monitors else "No"
        report_lines.append(
            f"| `{sc['scenario_id']}` | `{sc['action_taken']['name']}` | "
            f"{'Violation' if sc['ground_truth_violation'] else 'Safe'} | {flags_str} | {disagreement} |"
        )

    report_lines.extend(
        [
            "",
            "## 7. Scientific Observations & Limitations",
            "",
            "1. **Detection vs Alarm Rate**: Increasing monitor sensitivity (e.g., via disjunctive fusion) "
            "often improves recall at the risk of higher false-positive rates.",
            "2. **Correlated Failure Modes**: Rule-based monitors depend on explicit action definitions, "
            "whereas heuristic monitors depend on string patterns; adversaries could bypass both by renaming actions.",
            "3. **Auditing**: Raw scenario traces, decisions, and metadata are saved in `.uaise_runs/` "
            "for complete auditability.",
        ]
    )

    return "\n".join(report_lines)
