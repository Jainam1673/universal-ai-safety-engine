# UAISE Development Roadmap & Task Tracker

## Milestone 0: Repository Audit and Baseline
- [x] Inspect existing repository structure, tools (`uv`, Python version, Git status).
- [x] Transition Python configuration to Python 3.12 baseline.
- [x] Establish `src/` layout and packaging structure (`src/uaise`).

## Milestone 1: Project Foundation
- [x] Configure `pyproject.toml` with `uaise` CLI entry point, Hatchling build system, and dev dependencies.
- [x] Verify `uv sync` generates valid lockfile (`uv.lock`).
- [x] Verify `uv run uaise --help` and `uv run uaise doctor`.
- [x] Set up unit testing with `pytest`, linting with `ruff`, and strict type checking with `mypy`.
- [x] Implement initial domain types and validated configuration schemas.

## Milestone 2: Offline Research Vertical Slice
- [x] Implement synthetic reward-hacking/oversight benchmark (`toy_reward_hacking`).
- [x] Implement deterministic scripted agents (`safe`, `reward_hacker`, `opportunistic`).
- [x] Define explicit, independent ground-truth outcomes for all scenarios (`is_action_violation`).
- [x] Implement deterministic rule-based monitor (`ActionConstraintMonitor`).
- [x] Build the core evaluation runner (`EvaluationRunner`).
- [x] Implement core evaluation metrics (Confusion Matrix, Precision, Recall, F1, FPR, zero-denominator conventions).
- [x] Verify reproducible offline run (`uv run uaise demo --seed 42`).

## Milestone 3: Persistence and Reporting
- [x] Design lightweight JSON experiment record persistence (`RunStorage` in `.uaise_runs/`).
- [x] Implement structured run metadata capturing (environment, seeds, commit, configs).
- [x] Build Markdown research report generator (`generate_markdown_report`).
- [x] Enable `uv run uaise report --latest`.

## Milestone 4: Multiple Monitors & Evidence Fusion
- [x] Implement behavioral trajectory/pattern monitor (`BehavioralHeuristicMonitor`).
- [x] Implement evidence fusion engine (`FusedMonitor`) supporting `any_flag`, `all_flag`, and `weighted_average`.
- [x] Preserve individual monitor decisions, risk scores, and disagreement metrics in reports and JSON traces.
- [x] Run comparative evaluation on synthetic benchmark.

## Milestone 5: Optional Hosted LLM Testing
- [x] Implement opt-in hosted model adapter (`HostedOpenAIModel` for OpenAI-compatible chat completions).
- [x] Implement `LLMAgent` and `LLMJudgeMonitor` interfaces.
- [x] Ensure full mock coverage using `httpx.MockTransport` and `MockModel` with zero billable calls during testing.
- [x] Graceful degradation and actionable diagnostics when `UAISE_API_KEY` is unconfigured.

## Milestone 6: Research-Quality Verification
- [x] Statistical uncertainty calculation: Empirical 95% bootstrap confidence intervals ($B=1,000$ iterations).
- [x] Integrate uncertainty intervals into `EvaluationRunResult` and Markdown research reports.
- [x] Document methodology and bootstrap protocols in `docs/RESEARCH_METHODOLOGY.md`.

## Milestone 7: Research Platform API & Auditing
- [x] Implement lightweight FastAPI research service (`uaise serve` / `src/uaise/api/app.py`).
- [x] Add tabular CSV and JSON auditing export commands (`uaise export`).

## Milestone 8: AI Safety Specialty Tracks
- [x] **Adversarial Robustness & Evasion**: Adaptive parameter-smuggling agent (`AdversarialEvasionAgent`) proving syntactic monitor blind spots and multi-monitor complementary detection.
- [x] **Formal Methods & Verification**: Invariant checking for continuous action state bounds (`StateInvariant`, `FormalContract`, `FormalVerifierMonitor`, `CyberPhysicalInvariantsBenchmark`).
- [x] **Canary Privacy Auditing**: Synthetic canary tracking and leakage detection across actions and rationales (`SyntheticCanary`, `CanaryTracker`, `PrivacyCanaryMonitor`, `CanaryPrivacyBenchmark`).
- [x] **Multi-Agent Containment**: Sub-agent delegation boundaries and capability escalation policies (`ContainmentPolicy`, `ContainmentMonitor`).
- [x] **Governance & Provenance Auditing**: Deterministic canonical SHA-256 manifest generation and integrity verification (`ProvenanceManifest`, `verify_run_integrity`, `uaise audit`).
- [x] **Mechanistic Interpretability**: Output distribution Shannon entropy and activation anomaly detection (`LogitEntropySignal`, `ActivationAnomalyMonitor`).
