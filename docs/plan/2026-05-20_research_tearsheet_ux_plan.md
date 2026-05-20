# Research Tearsheet and UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship priority 1 first, then priority 6: a deterministic research factor tearsheet / record template, followed by a small CLI entrypoint that makes the workflow easy to run without leaving the shared research/backtest evidence architecture.

**Architecture:** `qts.research` owns research evidence only. A new factor-tearsheet owner aggregates already-computed `FactorEvaluationResult` snapshots into deterministic JSON and manifest metrics. `ResearchSession` exposes a convenience recorder that writes the tearsheet artifact and indexes it through `ExperimentStore`. The CLI delegates to `ResearchSession` and does not parse market data, simulate fills, mutate runtime state, create target intents, or bypass `BacktestPipeline` for executable strategy evidence.

**Tech Stack:** Python dataclasses, `Decimal`, deterministic JSON artifacts, existing `FactorEvaluation`, `ExperimentManifestWriter`, `ExperimentStore`, `ResearchSession`, optional pandas via lazy import, argparse, pytest, guardrails, mypy.

---

## Domain Gates

Domain fact / invariant:
Research tearsheets summarize historical research evidence. They must not compute factor scores from forward returns, create orders or target intents, mutate account/portfolio/order state, or redefine backtest/paper/live execution semantics.

Correct owner or abstraction boundary:
`qts.factors` owns factor computation. `qts.research.factor_evaluation` owns per-snapshot factor metrics. The new `qts.research.tearsheet` owner aggregates per-snapshot research metrics and writes deterministic report artifacts. `ResearchSession` only delegates to those owners and records manifests through `ExperimentManifestWriter` / `ExperimentStore`.

Forbidden shortcut:
Do not add a research-only backtest engine, parse historical CSV rows in the tearsheet or CLI, import runtime/execution/broker/risk/account modules into `qts.research`, generate factor Python code, or make paper/live consume research artifacts directly.

Required gates / verification:
First red tests, focused research tests, CLI integration test, docs updates, public export checks, platform-freeze exceptions if new public classes are added, private-helper inspection, `make format`, `make lint`, `make guardrails`, `make typecheck`, `make test-unit`, `make test-integration`, `git diff --check`, and code-review-graph refresh/review.

## External Patterns Being Borrowed

- QuantConnect meta-analysis loads backtest, optimization, and live results into research for analysis and comparison; QTS should likewise make evidence comparison easy while keeping execution in the normal runtime path.
- Qlib Recorder centers experiment tracking around metrics, params, artifacts, and searchable records; QTS already has `ResearchExperimentRecorder` and should add a standard record template for factor research evidence.
- Pyfolio popularized the idea of a tear sheet as a compact performance/risk analysis artifact; QTS should start with deterministic JSON/pandas rows before adding charts.

## Scope

In scope for priority 1:

- Add a deterministic factor-tearsheet module that aggregates `FactorEvaluationResult` snapshots.
- Aggregate metrics: mean rank IC, positive Rank IC rate, mean long-short spread, mean coverage, minimum coverage, mean turnover when available, turnover observation count, snapshot count, date range, and unique missing symbols.
- Write a deterministic JSON tearsheet artifact that contains summary metrics plus per-snapshot rows.
- Expose notebook-friendly rows and pandas frame helpers.
- Add `ResearchSession.factor_tearsheet(...)`, `factor_tearsheet_frame(...)`, and `record_factor_tearsheet(...)`.
- Record the tearsheet artifact in an experiment manifest and store index through existing owners.

In scope for priority 6:

- Add `scripts/run_research.py` with a `factor-tearsheet` command that records a tearsheet from one or more existing factor-evaluation artifact JSON files.
- Add a `runs` command that lists or metric-sorts existing `ExperimentStore` records for a research config.
- Update research docs with the notebook and CLI quickstart.

Out of scope:

- Plot rendering, HTML/PDF reports, and chart styling.
- Running factor computation from the CLI.
- Running or shortcutting backtests from the tearsheet path.
- Promotion gates that approve factors for paper/live.
- New production dependencies.

## Acceptance Criteria

- `FactorEvaluationTearsheet.from_evaluations(...)` rejects empty inputs and mixed factor identity, sorts snapshots by `as_of`, and produces deterministic rows.
- Summary metrics are deterministic `Decimal` values serialized as canonical strings with at most 10 fractional decimals.
- `mean_turnover` is `None` when no snapshot has turnover, otherwise averages only observed turnover values.
- `FactorEvaluationTearsheetArtifactWriter.write(...)` writes stable JSON bytes ending with a newline.
- `FactorEvaluationTearsheet.from_artifact_paths(...)` round-trips artifacts produced by `FactorEvaluationArtifactWriter`.
- `ResearchSession.record_factor_tearsheet(...)` writes a tearsheet artifact, writes an experiment manifest under the session output root, and indexes it in `ExperimentStore`.
- The CLI `factor-tearsheet` command uses `ResearchSession.record_factor_tearsheet(...)` and prints artifact/manifest/store evidence paths.
- The CLI `runs` command reads the existing store and can sort by a metric without touching runtime state.
- Docs explicitly state that tearsheets are research evidence only and paper/live can only use reviewed `qts.factors` code through normal strategy/backtest paths.

## Verification Evidence To Record

- [x] First red: `uv run pytest tests/unit/research/test_tearsheet.py::test_factor_tearsheet_aggregates_snapshot_metrics -q` -> red: `ModuleNotFoundError: No module named 'qts.research.tearsheet'`.
- [x] Focused unit green: `uv run pytest tests/unit/research/test_tearsheet.py -q` -> 8 passed.
- [x] Session integration green: `uv run pytest tests/integration/test_research_session_facade.py::test_research_session_records_factor_tearsheet_without_changing_backtest_path -q` -> 1 passed.
- [x] Safety red/green: `uv run pytest tests/integration/test_research_session_facade.py::test_research_session_record_factor_tearsheet_rejects_path_like_experiment_id -q` -> first red `DID NOT RAISE`; final green 1 passed.
- [x] Determinism red/green: `uv run pytest tests/integration/test_research_session_facade.py::test_research_session_record_factor_tearsheet_hash_is_artifact_order_independent -q` -> first red mismatched `config_hash`; final green 1 passed.
- [x] Research import boundary red/green: `uv run pytest tests/unit/scripts/test_verify_guardrails.py::test_research_package_has_no_runtime_execution_risk_or_portfolio_imports -q` -> first red no violation; final green 1 passed.
- [x] CLI integration green: `uv run pytest tests/integration/test_run_research_cli.py -q` -> 2 passed.
- [x] Focused research green: `uv run pytest tests/unit/research tests/integration/test_research_session_facade.py tests/integration/test_research_session_factor_discovery.py tests/integration/test_run_research_cli.py -q` -> 131 passed.
- [x] Private helper inspection: `rg -n "^def _|^class _" backend/src/qts/research/tearsheet.py backend/src/qts/research/session.py scripts/run_research.py backend/src/qts/quality/guardrails.py` -> only CLI module-level helpers in the new CLI, class-owned research helpers, and a shared guardrail rule helper.
- [x] `make format` -> 671 files left unchanged on final run.
- [x] `make lint` -> All checks passed.
- [x] `make guardrails` -> Architecture guardrails passed.
- [x] `make typecheck` -> Success: no issues found in 651 source files.
- [x] `make test-unit` -> 1105 passed.
- [x] `make test-integration` -> 130 passed, 4 skipped.
- [x] `make test-anchor` -> 136 passed, 2 skipped.
- [x] `git diff --check` -> no output.
- [x] code-review-graph `build_or_update_graph_tool` -> final full build parsed 703 files, 6260 nodes, 51403 edges.
- [x] code-review-graph `detect_changes_tool` -> final: 15 changed files, risk 0.60, 0 affected flows.
- [x] code-review-graph `get_affected_flows_tool` -> final: 0 affected flows.

## File Structure

- Create `backend/src/qts/research/tearsheet.py`
  - Public classes: `FactorEvaluationTearsheet`, `FactorEvaluationTearsheetMetrics`, `FactorEvaluationTearsheetArtifactWriter`.
  - Owns aggregation, artifact parsing, deterministic JSON payloads, and pandas conversion.
- Modify `backend/src/qts/research/session.py`
  - Add facade methods for building, framing, and recording factor tearsheets.
- Modify `backend/src/qts/research/__init__.py`
  - Export public tearsheet types.
- Modify `docs/architecture/platform_freeze_exceptions.yaml`
  - Register new public classes if required by guardrails.
- Add `scripts/run_research.py`
  - Owns CLI argument parsing and delegates to `ResearchSession`.
- Add `tests/unit/research/test_tearsheet.py`
  - Covers aggregation, deterministic JSON, artifact round-trip, pandas helper, and public exports.
- Modify `tests/integration/test_research_session_facade.py`
  - Covers `ResearchSession.record_factor_tearsheet(...)` while preserving backtest path.
- Add `tests/integration/test_run_research_cli.py`
  - Covers `factor-tearsheet` and `runs` commands.
- Modify `docs/research/research_session_v1.md`
  - Add notebook and CLI usage.

## Parallelization Plan

- Lane A, priority 1 core: `tearsheet.py`, unit tests, public exports. This must finish before CLI behavior can be fully green.
- Lane B, priority 6 UX analysis: CLI shape, docs wording, and integration-test fixture design can proceed while Lane A is in progress.
- Lane C, verification: graph review, private-helper inspection, and focused/broad command execution run after both lanes merge.

Implementation is sequential at the shared export/docs integration points to avoid conflicts. Analysis and review are parallelized where write sets do not overlap.

## Task 1: Priority 1 Core Tearsheet

**Files:**

- Create: `backend/src/qts/research/tearsheet.py`
- Create: `tests/unit/research/test_tearsheet.py`
- Modify: `backend/src/qts/research/__init__.py`
- Modify: `docs/architecture/platform_freeze_exceptions.yaml`

- [x] Write failing aggregation and deterministic-artifact tests.
- [x] Run the first red gate and record the missing-module failure.
- [x] Implement `FactorEvaluationTearsheetMetrics`, `FactorEvaluationTearsheet`, and `FactorEvaluationTearsheetArtifactWriter`.
- [x] Export public types and register platform-freeze exceptions if guardrails require them.
- [x] Run `uv run pytest tests/unit/research/test_tearsheet.py -q`.

## Task 2: Priority 1 ResearchSession Record Template

**Files:**

- Modify: `backend/src/qts/research/session.py`
- Modify: `tests/integration/test_research_session_facade.py`
- Modify: `docs/research/research_session_v1.md`

- [x] Write a failing integration test for `session.record_factor_tearsheet(...)`.
- [x] Implement `factor_tearsheet(...)`, `factor_tearsheet_frame(...)`, and `record_factor_tearsheet(...)`.
- [x] Update durable research docs with notebook usage and the evidence-only invariant.
- [x] Run the session integration test and focused research tests.

## Task 3: Priority 6 CLI UX

**Files:**

- Create: `scripts/run_research.py`
- Create: `tests/integration/test_run_research_cli.py`
- Modify: `docs/research/research_session_v1.md`

- [x] Write failing CLI integration tests for `factor-tearsheet` and `runs`.
- [x] Implement the CLI by delegating to `ResearchSession`.
- [x] Update docs with exact commands.
- [x] Run `uv run pytest tests/integration/test_run_research_cli.py -q`.

## Task 4: Verification, Review, and Commit

- [x] Run focused research and CLI tests.
- [x] Inspect private helpers in changed Python files.
- [x] Run normal checks: `make format`, `make lint`, `make guardrails`, `make typecheck`, `make test-unit`, `make test-integration`, `git diff --check`.
- [x] Refresh code-review graph and inspect change/flow impact.
- [x] Commit with message `Add research tearsheet workflow`.
