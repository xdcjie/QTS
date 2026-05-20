# Research Session Facade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a notebook/script-friendly `ResearchSession` facade that makes research workflows simple while preserving the existing backtest/paper/live parity architecture.

**Architecture:** `ResearchSession` is an orchestration facade in `qts.research`. It owns config loading and ergonomic methods, but delegates data reads to `ResearchBook`, executable backtests to `BacktestPipeline`, optimization sweeps to `BacktestPipelineRunner`, and evidence indexing to `ExperimentStore`; it does not parse CSVs, simulate fills, or create a research-only execution path.

**Tech Stack:** Python dataclasses, YAML via existing `pyyaml`, existing `ResearchBook`, existing `BacktestPipeline`, existing `BacktestPipelineRunner`, existing `ExperimentStore`, optional pandas via local import, pytest.

---

## Domain Gates

Domain fact / invariant:
Research convenience APIs may reduce user ceremony, but executable performance evidence must still come from the same backtest pipeline used by normal backtests.

Correct owner or abstraction boundary:
`qts.research.session` owns the facade and config. Historical semantics stay in data/catalog/bar owners. Backtest wiring stays in `qts.backtest.pipeline`. Experiment indexing stays in `qts.research.experiment_store`.

Forbidden shortcut:
Do not hand-roll bars, portfolio/account state, risk, order, fill simulation, or CSV parsing inside `ResearchSession`.

Required gates / verification:
Unit tests for config validation and facade delegation, integration tests proving optimize uses `BacktestPipelineRunner`, `make guardrails`, `make typecheck`, and focused research tests.

## File Structure

- Create `backend/src/qts/research/session.py`: `ResearchSessionConfig`, `ResearchSession`, `ResearchOptimizationSummary`, comparison helpers.
- Modify `backend/src/qts/research/__init__.py`: export the public facade types.
- Create `tests/unit/research/test_research_session.py`: config validation, parameter-grid conversion, store listing/comparison behavior.
- Create `tests/integration/test_research_session_facade.py`: YAML-driven session loads existing backtest config, reads history, runs backtest, optimizes via shared pipeline, records experiment evidence.
- Add `configs/research/quickstart.yaml`: sample research config referencing existing data and a backtest config.
- Add `docs/research/research_session_v1.md`: public contract and architecture constraints.
- Update `docs/architecture/platform_freeze_exceptions.yaml`: expiring class-inventory exceptions if guardrails require them.
- Regenerate source inventory HTML if class/file inventory tests require it.

## Task 1: Config and Facade Shape

- [x] **Step 1: Write failing unit tests**

Test `ResearchSessionConfig.from_yaml(...)` with a minimal config:

```yaml
data:
  config: configs/data/historical.local.yaml
  catalog: research_futures
  roots: [GC]
  timeframe: 1m
backtest_config: configs/backtest.gc_si.example.yaml
store: runs/research/quickstart
output_root: runs/research/quickstart/backtests
objective_metric: sharpe_ratio
```

Assert that:
- paths are normalized relative to the YAML file directory when relative paths exist there, otherwise relative to the repo root;
- empty roots, missing catalog, and missing backtest config are rejected;
- `ResearchSession.from_yaml(...)` exposes `book` and `store`.

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py -q
```

Expected: fail because `qts.research.ResearchSession` is not exported.

- [x] **Step 2: Implement minimal config/session**

Implement `ResearchSessionConfig.from_yaml(...)`, `ResearchSession.from_yaml(...)`, `ResearchSession.book`, `ResearchSession.store`, `ResearchSession.history(...)`, and `ResearchSession.history_frame(...)`.

- [x] **Step 3: Rerun tests**

```bash
uv run pytest tests/unit/research/test_research_session.py tests/unit/research/test_research_book.py -q
```

Expected: pass.

## Task 2: Backtest and Optimize Facade

- [x] **Step 1: Write failing integration tests**

Create an integration fixture with a tiny local historical dataset and backtest YAML. Assert:
- `ResearchSession.run_backtest(strategy_params={"quantity": "2"})` returns a manifest path from `BacktestPipeline`;
- `ResearchSession.optimize(parameters={...})` returns ranked results from `BacktestPipelineRunner`;
- every optimizer run writes a normal backtest manifest.

Run:

```bash
uv run pytest tests/integration/test_research_session_facade.py -q
```

Expected: fail because backtest/optimize facade methods do not exist.

- [x] **Step 2: Implement run_backtest and optimize**

`run_backtest(...)` must call `BacktestPipeline.from_yaml(...).with_strategy_params(...).build_engine().run_streaming(...)`.

`optimize(...)` must build a `ParameterGrid` from a mapping of parameter name to values and call `BacktestPipelineRunner().run(BacktestPipelineJob(...))`.

- [x] **Step 3: Rerun integration tests**

```bash
uv run pytest tests/integration/test_research_session_facade.py tests/integration/test_optimizer_consumes_backtest_config.py -q
```

Expected: pass.

## Task 3: Store, Compare, and Docs

- [x] **Step 1: Write failing tests**

Add tests for:
- `ResearchSession.record_manifest(...)` delegating to `ExperimentStore`;
- `ResearchSession.list_runs(limit=...)`;
- `ResearchSession.compare_runs(metric="sharpe_ratio")` returning records sorted descending by numeric metric;
- `ResearchSession.compare_frame(...)` returning a pandas DataFrame with experiment id, strategy, metric, manifest path, and recorded time.

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py -q
```

Expected: fail because these methods do not exist.

- [x] **Step 2: Implement store/compare helpers**

Keep comparison read-only and based only on `ExperimentStoreRecord.metrics`; do not read backtest internals.

- [x] **Step 3: Add config and docs**

Add `configs/research/quickstart.yaml` and `docs/research/research_session_v1.md`. The doc must state that executable research evidence goes through `BacktestPipeline` / `BacktestPipelineRunner`.

## Task 4: Verification

- [x] **Step 1: Inspect private helpers**

```bash
rg -n "^def _|^class _" backend/src/qts/research/session.py
```

Expected: private helpers belong to `ResearchSessionConfig`, `ResearchSession`, or pure conversion functions shared by the module.

- [x] **Step 2: Run focused checks**

```bash
uv run pytest tests/unit/research tests/integration/test_research_session_facade.py tests/integration/test_research_book_historical_catalog.py tests/integration/test_optimizer_consumes_backtest_config.py -q
make guardrails
make typecheck
```

Expected: all pass.

- [x] **Step 3: Run normal-code checks**

```bash
make format
make lint
make test-unit
make test-integration
make test-anchor
```

Expected: all pass or report exact blockers.
