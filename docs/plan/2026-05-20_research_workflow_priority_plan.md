# Research Workflow Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for inline execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the first prioritized research-workflow slice: experiment indexing, optimizer publication into that index, and a small notebook-friendly `ResearchBook` facade.

**Architecture:** Keep research read-only with respect to runtime trading state. `qts.research` owns deterministic manifests and the new experiment registry; optimizer code may publish completed run evidence only after the shared backtest pipeline has produced normal manifests. `ResearchBook` remains a facade over historical data boundaries and returns optional pandas frames without making domain models depend on pandas.

**Tech Stack:** Python dataclasses, JSON artifacts, existing `qts.research`, existing optimizer and backtest pipeline, optional pandas for research-facing tabular output, pytest, guardrails.

---

## Domain Gates

Domain fact / invariant:
Research artifacts are evidence about completed experiments. They must not mutate runtime, account, order, broker, or portfolio state, and they must not redefine dataset identity, bar/session semantics, or backtest/live execution paths.

Correct owner or abstraction boundary:
`qts.research` owns experiment manifests, experiment indexing, and notebook-facing read-only research helpers. `qts.research.optimizer` owns publication of completed optimizer evidence after normal backtest manifests exist. `qts.backtest` remains the owner of executable backtest flow.

Forbidden shortcut:
Do not add a research-only backtest shortcut, direct runtime import from `qts.research`, ad hoc CSV parsing in notebook helpers, or a new storage dependency without benchmark evidence.

Required gates / verification:
Focused research unit tests, optimizer integration test, research import guardrail, `make guardrails`, `make typecheck`, and private-helper inspection for changed Python files.

## File Structure

- Create `backend/src/qts/research/experiment_store.py`: deterministic JSONL index for research experiment manifests.
- Modify `backend/src/qts/research/__init__.py`: export the public store types.
- Modify `scripts/run_optimizer.py`: optional `--experiment-store` and publication of validation summary evidence.
- Modify `backend/src/qts/research/research_book.py`: add notebook-friendly `history_rows(...)` and `history_frame(...)`.
- Modify `docs/research/research_book_v1.md`: document the new read-only facade methods.
- Create `tests/unit/research/test_experiment_store.py`: unit tests for indexing, query order, duplicate replacement, and manifest validation.
- Modify `tests/integration/test_optimizer_validation_cli.py`: verify CLI publishes optimizer validation evidence to the store.
- Modify `tests/unit/research/test_research_book.py` and `tests/integration/test_research_book_historical_catalog.py`: verify row and pandas-frame behavior.

## Task 1: ExperimentStore Registry

- [x] **Step 1: Write failing unit tests**

Add tests proving:
- `ExperimentStore.record_manifest(...)` indexes an existing manifest and persists deterministic JSONL.
- `ExperimentStore.list_runs()` returns most recent records first.
- recording the same experiment id replaces the prior record.
- missing manifest path is rejected.

Run:

```bash
uv run pytest tests/unit/research/test_experiment_store.py -q
```

Expected: fail because `qts.research.ExperimentStore` is not exported.

- [x] **Step 2: Implement minimal store**

Create `ExperimentStoreRecord` and `ExperimentStore` in `backend/src/qts/research/experiment_store.py`. Store one JSON object per experiment id in `experiments.jsonl`, sorted by `recorded_at` and `experiment_id` for deterministic bytes. Read existing records on each write, replace by experiment id, and expose `list_runs(limit: int | None = None)`.

- [x] **Step 3: Export public API and rerun tests**

Update `backend/src/qts/research/__init__.py` and rerun:

```bash
uv run pytest tests/unit/research/test_experiment_store.py tests/unit/research/test_experiment_manifest.py -q
```

Expected: pass.

## Task 2: Optimizer Publication

- [x] **Step 1: Write failing integration test**

Extend `tests/integration/test_optimizer_validation_cli.py` with a case that runs `scripts/run_optimizer.py` using both `--validation-output` and `--experiment-store`. Assert the store contains a record whose metrics include accepted/rejected counts and whose artifact hash points at the validation summary.

Run:

```bash
uv run pytest tests/integration/test_optimizer_validation_cli.py::test_optimizer_cli_publishes_validation_summary_to_experiment_store -q
```

Expected: fail because the CLI does not accept `--experiment-store`.

- [x] **Step 2: Implement CLI publication**

Add `--experiment-store` to `scripts/run_optimizer.py`. When supplied, require `--validation-output`, write the existing validation summary, then write an experiment manifest and record it with `ExperimentStore`. Use strategy name `optimizer`, strategy version `1`, dataset ids containing the backtest config path for pipeline runs or strategy module for factory runs, and metrics from the validation summary counts.

- [x] **Step 3: Rerun optimizer tests**

Run:

```bash
uv run pytest tests/integration/test_optimizer_validation_cli.py tests/integration/test_run_optimizer_cli_outputs_ranked_results.py tests/integration/test_optimizer_consumes_backtest_config.py -q
```

Expected: pass.

## Task 3: ResearchBook Notebook Facade

- [x] **Step 1: Write failing tests**

Add tests for:
- `ResearchHistoryFrame.rows()` returning deterministic dictionaries with timestamp, instrument id, OHLCV, timeframe, and completeness fields.
- `ResearchHistoryFrame.to_pandas()` returning a pandas `DataFrame` with the same row order.
- `ResearchBook.history_rows(request)` delegating through the existing `history(...)` path.

Run:

```bash
uv run pytest tests/unit/research/test_research_book.py tests/integration/test_research_book_historical_catalog.py -q
```

Expected: fail because the methods do not exist.

- [x] **Step 2: Implement minimal facade**

Add `ResearchHistoryFrame.rows()`, `ResearchHistoryFrame.to_pandas()`, and `ResearchBook.history_rows(...)`. Keep pandas import local to `to_pandas()` so domain/runtime models do not depend on pandas at import time.

- [x] **Step 3: Update docs and rerun tests**

Update `docs/research/research_book_v1.md` to document rows and pandas-frame helpers. Rerun the focused research tests.

## Task 4: Verification

- [x] **Step 1: Inspect private helpers**

```bash
rg -n "^def _|^class _" backend/src/qts/research/experiment_store.py backend/src/qts/research/research_book.py scripts/run_optimizer.py
```

Expected: private helpers either belong to their owning class or are CLI/framework helpers.

- [x] **Step 2: Run focused verification**

```bash
uv run pytest tests/unit/research tests/integration/test_optimizer_validation_cli.py tests/integration/test_run_optimizer_cli_outputs_ranked_results.py tests/integration/test_optimizer_consumes_backtest_config.py tests/integration/test_research_book_historical_catalog.py -q
make guardrails
make typecheck
```

Expected: all pass.

- [x] **Step 3: Broader normal-code checks**

```bash
make format
make lint
make test-unit
```

Expected: all pass, or report exact blockers.
