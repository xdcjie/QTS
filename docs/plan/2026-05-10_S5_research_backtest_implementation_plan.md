# S5 Research-Grade Backtest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete research-grade backtest system over the local GC and SI historical futures datasets.

**Architecture:** Keep historical data, Strategy SDK, backtest simulation, portfolio accounting, risk, and reporting as separate boundaries. Historical files under `historical/` become reproducible datasets with explicit provenance and validation before the backtest engine consumes them. The engine remains deterministic and uses the same Strategy SDK intent path as paper/live simulation where practical.

**Tech Stack:** Python 3.11+, pandas where useful for research-facing tabular work, existing qts domain/runtime modules, pytest, ruff, mypy, exchange-calendars behind project interfaces.

---

## Current Data Facts

- `historical/data/gc.csv`: 15,142,967 lines including header.
- `historical/data/si.csv`: 9,830,594 lines including header.
- CSV columns: `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol`.
- `historical/chains/GC.json`: root `GC`, top-level multiplier `100.0`, tick size `0.1`, timezone `US/Eastern`, 224 contracts.
- `historical/chains/SI.json`: root `SI`, top-level multiplier `5000.0`, tick size `0.005`, timezone `US/Eastern`, 230 contracts.
- CSV data includes outright symbols such as `GCQ0` and spread symbols such as `GCN0-GCQ0`; spread rows must not silently enter outright futures backtests.

## Non-Goals For S5

- No live trading enablement.
- No real IBKR SDK order submission.
- No frontend research workbench.
- No broad distributed runtime.
- No new storage dependency until a benchmark justifies it.

## File Map

Create:

- `backend/src/qts/data/historical/__init__.py`
- `backend/src/qts/data/historical/chains.py`
- `backend/src/qts/data/historical/csv_dataset.py`
- `backend/src/qts/data/historical/gc_si.py`
- `backend/src/qts/backtest/config.py`
- `backend/src/qts/backtest/report.py`
- `backend/src/qts/backtest/metrics.py`
- `backend/src/qts/backtest/events.py`
- `backend/src/qts/backtest/research_runner.py`
- `configs/backtest.gc_si.example.yaml`
- `scripts/run_research_backtest.py`
- `docs/plan/status/S5_research_backtest_status.md`
- `tests/unit/data/test_historical_chains.py`
- `tests/unit/data/test_historical_csv_dataset.py`
- `tests/integration/test_gc_si_historical_loading.py`
- `tests/unit/backtest/test_backtest_config.py`
- `tests/unit/backtest/test_backtest_report_metrics.py`
- `tests/integration/test_research_backtest_gc_si.py`
- `tests/replay/test_research_backtest_determinism.py`

Modify:

- `backend/src/qts/backtest/engine.py`
- `backend/src/qts/backtest/__init__.py`
- `backend/src/qts/strategy_sdk/context.py`
- `backend/src/qts/strategy_sdk/data_view.py`
- `backend/src/qts/strategy_sdk/indicators.py`
- `backend/src/qts/portfolio/position_book.py`
- `backend/src/qts/portfolio/valuation.py`
- `backend/src/qts/data/__init__.py`
- `Makefile`

## Loop Protocol

Each loop implements exactly one task ID below.

For every task:

1. State the invariant before coding.
2. Write the failing test first.
3. Run the focused test and confirm the failure is relevant.
4. Implement the minimum code.
5. Run focused checks.
6. Run wider checks when the task touches shared behavior.
7. Update `docs/plan/status/S5_research_backtest_status.md`.

Default focused checks:

```bash
uv run ruff format <changed-files>
uv run ruff check <changed-files>
uv run mypy --strict <changed-python-files>
uv run pytest <focused-test-file>
```

Broader checks by area:

```bash
make test-unit
make test-integration
make test-anchor
make test-replay
```

---

# Task Breakdown

## S5-00 Baseline And Historical Inventory

### S5-00-T01 Record Historical Inventory

**Invariant:** Full GC/SI datasets are external research inputs; backtest behavior must reference them through metadata, not hidden file assumptions.

**Files:**
- Create: `docs/plan/status/S5_research_backtest_status.md`

**Steps:**

- [ ] Write an inventory section with file paths, line counts, columns, chain metadata, and known spread-symbol rows.
- [ ] Record that live trading remains out of scope.
- [ ] Run:

```bash
wc -l historical/data/gc.csv historical/data/si.csv
head -5 historical/data/gc.csv
head -5 historical/data/si.csv
python - <<'PY'
import json
from pathlib import Path
for path in [Path("historical/chains/GC.json"), Path("historical/chains/SI.json")]:
    payload = json.loads(path.read_text())
    print(path, payload["root"], payload["multiplier"], payload["tick_size"], len(payload["contracts"]))
PY
```

**Acceptance:**
- Status doc records the current dataset facts.
- No implementation files change.

## S5-01 Historical Contract Chain Support

### S5-01-T01 Parse GC/SI Chain Metadata

**Invariant:** Contract multiplier, tick size, expiry, first notice day, currency, and exchange calendar are contract facts. They must come from chain metadata, not from CSV price rows.

**Files:**
- Create: `backend/src/qts/data/historical/chains.py`
- Test: `tests/unit/data/test_historical_chains.py`

**Steps:**

- [ ] Add failing tests for `load_historical_chain(Path("historical/chains/GC.json"))`.
- [ ] Assert root, timezone, top-level tick size, top-level multiplier, and contract count.
- [ ] Assert `GCM0` parses with expiry and first notice day.
- [ ] Add the minimal dataclasses `HistoricalChain` and `HistoricalContract`.
- [ ] Implement JSON parsing with `Decimal` for numeric contract facts.
- [ ] Run `uv run pytest tests/unit/data/test_historical_chains.py`.

**Acceptance:**
- GC and SI chain JSON parse without leaking raw JSON dictionaries to callers.
- Numeric metadata uses `Decimal`.
- Missing required chain fields raise `ValueError`.

### S5-01-T02 Map Historical Symbols To InstrumentId

**Invariant:** Internal backtests use `InstrumentId`; raw symbols such as `GCQ0` and `SIU4` remain source/boundary identifiers.

**Files:**
- Modify: `backend/src/qts/data/historical/chains.py`
- Test: `tests/unit/data/test_historical_chains.py`

**Steps:**

- [ ] Add failing test: `chain.instrument_id_for_symbol("GCQ0") == InstrumentId("FUTURE.CME.GC.GCQ0")`.
- [ ] Add failing test: spread symbol `GCN0-GCQ0` is rejected as not an outright contract.
- [ ] Implement `HistoricalChain.instrument_id_for_symbol`.
- [ ] Implement `HistoricalChain.is_outright_symbol`.
- [ ] Run `uv run pytest tests/unit/data/test_historical_chains.py`.

**Acceptance:**
- Outright contract symbols map to stable internal IDs.
- Spread symbols are classified and excluded unless a future spread feature explicitly adds support.

## S5-02 CSV Dataset Reader And Metadata

### S5-02-T01 Describe Historical CSV Dataset

**Invariant:** Dataset identity must include source path, instrument root, timeframe, timezone policy, normalization policy, and content reference.

**Files:**
- Create: `backend/src/qts/data/historical/csv_dataset.py`
- Test: `tests/unit/data/test_historical_csv_dataset.py`

**Steps:**

- [ ] Add failing test for `describe_csv_dataset(Path("historical/data/gc.csv"), root="GC")`.
- [ ] Assert expected columns exactly match the current CSV header.
- [ ] Assert dataset metadata includes root, path, row count if requested, and source hash policy.
- [ ] Implement a cheap header reader that does not load the whole 2.5GB dataset.
- [ ] Implement optional row counting behind an explicit flag.
- [ ] Run `uv run pytest tests/unit/data/test_historical_csv_dataset.py`.

**Acceptance:**
- Header inspection is fast and does not materialize all rows.
- Metadata distinguishes GC and SI datasets.
- Invalid column order fails explicitly.

### S5-02-T02 Stream CSV Rows Into Bars

**Invariant:** Historical CSV rows become `Bar` domain objects only after timestamp, OHLC, volume, symbol, and contract identity are valid.

**Files:**
- Modify: `backend/src/qts/data/historical/csv_dataset.py`
- Test: `tests/unit/data/test_historical_csv_dataset.py`

**Steps:**

- [ ] Add failing test using a temporary CSV with two outright rows and one spread row.
- [ ] Assert only outright rows are emitted by default.
- [ ] Assert emitted bars have UTC-aware timestamps and `[start,end)` one-minute intervals.
- [ ] Implement `iter_historical_bars(csv_path, chain, timeframe="1m")`.
- [ ] Use Python `csv.DictReader` and yield bars lazily.
- [ ] Run `uv run pytest tests/unit/data/test_historical_csv_dataset.py`.

**Acceptance:**
- Reader is streaming.
- Outright-only default is enforced.
- Spread rows are counted in reader stats but not emitted as outright bars.

### S5-02-T03 Add GC/SI Dataset Convenience Loader

**Invariant:** Research code should not know the physical historical file layout.

**Files:**
- Create: `backend/src/qts/data/historical/gc_si.py`
- Test: `tests/integration/test_gc_si_historical_loading.py`

**Steps:**

- [ ] Add failing test for `load_gc_si_catalog(Path("historical"))`.
- [ ] Assert catalog has roots `GC` and `SI`.
- [ ] Assert each root has chain path, CSV path, row count disabled by default, and dataset metadata.
- [ ] Implement catalog loader with explicit paths.
- [ ] Run `uv run pytest tests/integration/test_gc_si_historical_loading.py`.

**Acceptance:**
- Catalog creation does not scan all rows by default.
- Missing `historical/data/gc.csv`, `historical/data/si.csv`, `historical/chains/GC.json`, or `historical/chains/SI.json` fails with clear error.

## S5-03 Historical Data Validation Gate

### S5-03-T01 Validate Sampled GC/SI Bars

**Invariant:** Invalid OHLC, duplicate intervals, non-monotonic bars, and spread rows must not silently enter research backtests.

**Files:**
- Modify: `backend/src/qts/data/historical/csv_dataset.py`
- Test: `tests/unit/data/test_historical_csv_dataset.py`

**Steps:**

- [ ] Add failing test for `validate_historical_sample` using rows with invalid OHLC and a spread symbol.
- [ ] Assert invalid OHLC is `ERROR`.
- [ ] Assert spread row is reported as excluded, not converted to `Bar`.
- [ ] Implement sample validator using existing `DataValidationReport` where possible.
- [ ] Run `uv run pytest tests/unit/data/test_historical_csv_dataset.py`.

**Acceptance:**
- Validation report is available before running a backtest.
- Spread exclusion is visible in validation stats.

### S5-03-T02 Add Full Dataset Validation CLI

**Invariant:** Full dataset validation is an explicit operator/research action because GC/SI files are large.

**Files:**
- Create: `scripts/validate_historical_gc_si.py`
- Test: `tests/integration/test_gc_si_historical_loading.py`
- Modify: `Makefile`

**Steps:**

- [ ] Add failing CLI smoke test that runs validation with `--sample-rows 1000`.
- [ ] Implement `scripts/validate_historical_gc_si.py --root historical --sample-rows 1000`.
- [ ] Write JSON validation output to `evidence/historical/`.
- [ ] Add `make validate-historical-sample`.
- [ ] Run `uv run pytest tests/integration/test_gc_si_historical_loading.py`.

**Acceptance:**
- Sample validation creates JSON evidence.
- Full validation can be invoked separately with `--full`.
- No test loads the full 2.5GB dataset unless explicitly marked slow.

## S5-04 Backtest Configuration And Run Identity

### S5-04-T01 Add BacktestRunConfig

**Invariant:** A research run is defined by explicit config, not by ad hoc constructor arguments.

**Files:**
- Create: `backend/src/qts/backtest/config.py`
- Test: `tests/unit/backtest/test_backtest_config.py`
- Create: `configs/backtest.gc_si.example.yaml`

**Steps:**

- [ ] Add failing test for `BacktestRunConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))`.
- [ ] Include fields: dataset root, roots, symbols, start, end, timeframe, initial cash, strategy class, strategy params, cost model, risk config.
- [ ] Implement dataclasses with validation.
- [ ] Implement stable `config_hash`.
- [ ] Run `uv run pytest tests/unit/backtest/test_backtest_config.py`.

**Acceptance:**
- Config validation rejects empty roots, invalid date ranges, and non-positive initial cash.
- Stable hash changes when any material config field changes.

### S5-04-T02 Wire BacktestEngine To BacktestRunConfig

**Invariant:** The existing `BacktestEngine` API can remain, but research entrypoints should run from a full config object.

**Files:**
- Modify: `backend/src/qts/backtest/engine.py`
- Modify: `backend/src/qts/backtest/__init__.py`
- Test: `tests/integration/test_research_backtest_gc_si.py`

**Steps:**

- [ ] Add failing integration test for a small in-memory GC config.
- [ ] Implement `BacktestEngine.from_config(config, bars, strategy)`.
- [ ] Preserve existing constructor behavior.
- [ ] Ensure report includes `config_hash`.
- [ ] Run `uv run pytest tests/integration/test_research_backtest_gc_si.py`.

**Acceptance:**
- Existing backtest tests keep passing.
- Config-driven backtest produces deterministic run ID.

## S5-05 Research Event Loop Hardening

### S5-05-T01 Add Backtest Event Ordering

**Invariant:** Multi-instrument replay must be ordered deterministically by event time, instrument ID, and source sequence.

**Files:**
- Create: `backend/src/qts/backtest/events.py`
- Test: `tests/unit/backtest/test_replay_clock.py`

**Steps:**

- [ ] Add failing test for two bars at the same timestamp from GC and SI.
- [ ] Assert ordering is `(end_time, instrument_id.value, source_sequence)`.
- [ ] Implement `BacktestMarketDataEvent`.
- [ ] Implement `order_backtest_events`.
- [ ] Run `uv run pytest tests/unit/backtest/test_replay_clock.py`.

**Acceptance:**
- Same inputs always produce the same event order.
- Replay ordering is independent of input file ordering.

### S5-05-T02 Add Warmup Phase

**Invariant:** Indicator warmup data may initialize strategy state but must not allow orders unless explicitly enabled.

**Files:**
- Modify: `backend/src/qts/backtest/config.py`
- Modify: `backend/src/qts/backtest/engine.py`
- Test: `tests/integration/test_research_backtest_gc_si.py`

**Steps:**

- [ ] Add failing test: strategy emits target during warmup and no order is placed.
- [ ] Add `warmup_bars` to config.
- [ ] During warmup, set `ctx.data` and call `on_bar`, but discard trading intents.
- [ ] After warmup, process intents normally.
- [ ] Run `uv run pytest tests/integration/test_research_backtest_gc_si.py`.

**Acceptance:**
- Warmup is deterministic.
- Report records warmup bar count and trading bar count separately.

### S5-05-T03 Add Strategy Finalize Hook

**Invariant:** Strategies need a deterministic end-of-run hook for research summaries without mutating portfolio state after the clock stops.

**Files:**
- Modify: `backend/src/qts/strategy_sdk/strategy.py`
- Modify: `backend/src/qts/backtest/engine.py`
- Test: `tests/integration/test_research_backtest_gc_si.py`

**Steps:**

- [ ] Add failing test with strategy setting `self.finalized = True`.
- [ ] Add no-op `Strategy.finalize(ctx)`.
- [ ] Call finalize once after the last replay event.
- [ ] Assert no new target intents are processed after finalize.
- [ ] Run `uv run pytest tests/integration/test_research_backtest_gc_si.py`.

**Acceptance:**
- Finalize runs exactly once.
- Finalize cannot place orders in the completed report.

## S5-06 Futures-Aware Accounting And Execution Assumptions

### S5-06-T01 Apply Contract Multipliers In Backtest Fills

**Invariant:** GC and SI PnL/cash effects use contract multiplier; futures value is not equity share value.

**Files:**
- Modify: `backend/src/qts/backtest/engine.py`
- Modify: `backend/src/qts/portfolio/valuation.py`
- Test: `tests/anchor/test_portfolio_accounting_anchors.py`

**Steps:**

- [ ] Add failing anchor test for one GC contract moving from 2000.0 to 2001.0 with multiplier 100.
- [ ] Add failing anchor test for one SI contract moving by 0.005 with multiplier 5000.
- [ ] Pass contract metadata into backtest valuation.
- [ ] Keep stock accounting behavior unchanged.
- [ ] Run `uv run pytest tests/anchor/test_portfolio_accounting_anchors.py`.

**Acceptance:**
- Futures PnL uses `contracts * price_diff * multiplier`.
- Contract facts come from chain metadata.

### S5-06-T02 Add Explicit Commission And Slippage Models

**Invariant:** Research results must include the cost model that produced them, and changing costs must change fills and report hash.

**Files:**
- Modify: `backend/src/qts/backtest/config.py`
- Modify: `backend/src/qts/backtest/engine.py`
- Test: `tests/unit/backtest/test_backtest_report_metrics.py`

**Steps:**

- [ ] Add failing test for zero-cost fill preserving current behavior.
- [ ] Add failing test for fixed per-contract commission reducing cash/equity.
- [ ] Add failing test for slippage moving buy fill price up and sell fill price down.
- [ ] Implement simple fixed commission and basis-point slippage models.
- [ ] Run `uv run pytest tests/unit/backtest/test_backtest_report_metrics.py`.

**Acceptance:**
- Cost model is explicit in config and report.
- Report hash changes when cost settings change.

## S5-07 Research Report And Metrics

### S5-07-T01 Add BacktestReport Model

**Invariant:** A research report is a stable artifact containing inputs, events, orders, fills, portfolio snapshots, metrics, and hashes.

**Files:**
- Create: `backend/src/qts/backtest/report.py`
- Test: `tests/unit/backtest/test_backtest_report_metrics.py`

**Steps:**

- [ ] Add failing test constructing a minimal `BacktestReport`.
- [ ] Include run ID, config hash, dataset metadata, cost model, processed bars, orders, fills, equity curve, metrics, and report hash.
- [ ] Implement JSON serialization with sorted keys and Decimal-as-string conversion.
- [ ] Run `uv run pytest tests/unit/backtest/test_backtest_report_metrics.py`.

**Acceptance:**
- Report JSON is deterministic.
- Report includes enough provenance to reproduce the run.

### S5-07-T02 Add Equity Curve And Drawdown Metrics

**Invariant:** Research-grade reports must quantify performance from portfolio state, not from final cash only.

**Files:**
- Create: `backend/src/qts/backtest/metrics.py`
- Test: `tests/unit/backtest/test_backtest_report_metrics.py`

**Steps:**

- [ ] Add failing test for equity values `[100, 110, 105, 120]`.
- [ ] Assert total return, max drawdown, and number of equity points.
- [ ] Implement `compute_equity_metrics`.
- [ ] Run `uv run pytest tests/unit/backtest/test_backtest_report_metrics.py`.

**Acceptance:**
- Metrics are deterministic.
- Empty equity curve raises `ValueError`.

### S5-07-T03 Record Trade Ledger

**Invariant:** Every simulated fill must be auditable from strategy intent through risk, order, execution report, and account effect.

**Files:**
- Modify: `backend/src/qts/backtest/report.py`
- Modify: `backend/src/qts/backtest/engine.py`
- Test: `tests/integration/test_research_backtest_gc_si.py`

**Steps:**

- [ ] Add failing integration test that a one-order strategy produces one trade ledger row.
- [ ] Include order ID, instrument ID, side, quantity, fill price, commission, slippage, fill time, and source bar time.
- [ ] Populate ledger from normalized execution reports.
- [ ] Run `uv run pytest tests/integration/test_research_backtest_gc_si.py`.

**Acceptance:**
- Trade ledger row count equals accepted fill count.
- Duplicate fill IDs do not duplicate ledger entries.

## S5-08 Strategy Research SDK Improvements

### S5-08-T01 Add Strategy Data Subscription Declaration

**Invariant:** Research runs should know required assets/timeframes before replay starts.

**Files:**
- Modify: `backend/src/qts/strategy_sdk/context.py`
- Test: `tests/unit/strategy_sdk/test_context_symbol.py`

**Steps:**

- [ ] Add failing test for `ctx.subscribe(asset, timeframe="1m", warmup=60)`.
- [ ] Implement subscription records on `StrategyContext`.
- [ ] Validate positive warmup and non-empty timeframe.
- [ ] Run `uv run pytest tests/unit/strategy_sdk/test_context_symbol.py`.

**Acceptance:**
- Strategy can declare data needs without accessing market data internals.
- Backtest config can merge explicit config symbols with strategy subscriptions.

### S5-08-T02 Deterministic Indicator Warmup

**Invariant:** Indicator values must depend only on visible historical bars at or before `as_of`.

**Files:**
- Modify: `backend/src/qts/strategy_sdk/indicators.py`
- Modify: `backend/src/qts/backtest/engine.py`
- Test: `tests/unit/strategy_sdk/test_data_view.py`
- Test: `tests/integration/test_research_backtest_gc_si.py`

**Steps:**

- [ ] Add failing test for SMA value after exactly `window` visible bars.
- [ ] Add failing integration test that warmup produces ready indicators before trading starts.
- [ ] Implement explicit indicator update from completed bars.
- [ ] Run focused Strategy SDK and research backtest tests.

**Acceptance:**
- Indicator warmup is deterministic.
- Indicators do not see future bars.

## S5-09 GC/SI End-To-End Research Runner

### S5-09-T01 Add Research Backtest Runner

**Invariant:** Research users should run a GC/SI backtest from config without importing internals.

**Files:**
- Create: `backend/src/qts/backtest/research_runner.py`
- Create: `scripts/run_research_backtest.py`
- Test: `tests/integration/test_research_backtest_gc_si.py`

**Steps:**

- [ ] Add failing integration test using a small temporary GC/SI CSV fixture.
- [ ] Implement `run_research_backtest(config_path)`.
- [ ] Implement CLI: `python scripts/run_research_backtest.py --config configs/backtest.gc_si.example.yaml --output-dir runs/backtests`.
- [ ] Write report JSON to output directory.
- [ ] Run `uv run pytest tests/integration/test_research_backtest_gc_si.py`.

**Acceptance:**
- CLI runs on fixture data in tests.
- CLI can be pointed at `historical/` manually for full data.

### S5-09-T02 Add Moving Average GC/SI Example

**Invariant:** Example strategies must use only Strategy SDK public APIs.

**Files:**
- Create: `examples/strategies/gc_si_momentum.py`
- Test: `tests/anchor/test_strategy_sdk_boundaries.py`
- Test: `tests/integration/test_research_backtest_gc_si.py`

**Steps:**

- [ ] Add boundary test that the example imports only `qts.strategy_sdk` and standard library.
- [ ] Implement a simple GC/SI momentum or moving-average strategy.
- [ ] Run the strategy over fixture data.
- [ ] Run `uv run pytest tests/anchor/test_strategy_sdk_boundaries.py tests/integration/test_research_backtest_gc_si.py`.

**Acceptance:**
- Example strategy works unchanged through the research runner.
- No runtime, broker, risk, or order manager imports appear in the example.

## S5-10 Determinism, Performance, And Full-Data Gates

### S5-10-T01 Add Research Replay Determinism Test

**Invariant:** Same config, data, strategy code, and cost model must produce the same report hash.

**Files:**
- Create: `tests/replay/test_research_backtest_determinism.py`
- Modify: `Makefile`

**Steps:**

- [ ] Add failing replay test running the same fixture config twice.
- [ ] Assert report hashes are equal.
- [ ] Add `make test-research-replay`.
- [ ] Run `make test-research-replay`.

**Acceptance:**
- Replay determinism is verified independently from unit tests.
- Report hash changes when dataset metadata or cost config changes.

### S5-10-T02 Add Full Historical Smoke Gate

**Invariant:** Full GC/SI historical runs are expensive and must be explicit, observable, and resumable enough for operator use.

**Files:**
- Modify: `scripts/run_research_backtest.py`
- Create: `tests/soak/test_research_full_data_marker.py`
- Modify: `Makefile`

**Steps:**

- [ ] Add soak marker test documenting the manual full-data command.
- [ ] Add `make research-full-smoke` that runs a bounded date range over real `historical/`.
- [ ] Record elapsed time, processed rows, emitted bars, excluded spreads, and output report path.
- [ ] Run `make test-soak`.

**Acceptance:**
- Full-data command is opt-in.
- A bounded GC/SI date range can run without loading all rows into memory.

### S5-10-T03 Benchmark Storage Decision

**Invariant:** New storage dependencies require evidence that existing CSV streaming or JSONL storage is insufficient.

**Files:**
- Create: `docs/decision/2026-05-10_research_storage_decision.md`

**Steps:**

- [ ] Benchmark streaming CSV reader on a bounded GC and SI date range.
- [ ] Benchmark current JSONL file-backed store on the same range.
- [ ] Record memory, runtime, output size, and developer ergonomics.
- [ ] Decide whether to keep CSV streaming for S5 or propose a `pyarrow` dependency.

**Acceptance:**
- Storage decision is recorded before adding a new dependency.
- Dependency decision includes why pandas/stdlib/current store is insufficient if a new package is proposed.

---

## Recommended Execution Order

1. S5-00-T01
2. S5-01-T01
3. S5-01-T02
4. S5-02-T01
5. S5-02-T02
6. S5-02-T03
7. S5-03-T01
8. S5-03-T02
9. S5-04-T01
10. S5-04-T02
11. S5-05-T01
12. S5-05-T02
13. S5-05-T03
14. S5-06-T01
15. S5-06-T02
16. S5-07-T01
17. S5-07-T02
18. S5-07-T03
19. S5-08-T01
20. S5-08-T02
21. S5-09-T01
22. S5-09-T02
23. S5-10-T01
24. S5-10-T02
25. S5-10-T03

## Completion Criteria

S5 is complete when:

- GC/SI chain metadata is parsed into project types.
- GC/SI CSV rows stream into validated `Bar` objects without full-file materialization.
- Spread rows are excluded or explicitly classified.
- Backtest runs from `BacktestRunConfig`.
- Backtest replay supports deterministic multi-instrument event ordering.
- Warmup, finalize, DataView slicing, and indicator updates are deterministic.
- Futures contract multipliers affect valuation and PnL correctly.
- Cost assumptions affect fills and reports.
- Reports include provenance, trade ledger, equity curve, metrics, and stable hashes.
- A fixture-based GC/SI research backtest passes in CI.
- A bounded full-data historical smoke command exists for manual use.

