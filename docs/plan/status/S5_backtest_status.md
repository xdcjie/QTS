# S5 Backtest Status

## Scope

S5 builds a backtest path over local GC and SI historical futures
datasets. Live trading, real IBKR SDK order submission, frontend research UI,
distributed runtime work, and new storage dependencies are out of scope.

## S5-00-T01 Historical Inventory

Status: complete

Invariant: full GC/SI datasets are external historical inputs; backtest behavior
must reference them through metadata, not hidden file assumptions.

Observed commands:

```text
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

Dataset facts:

| Dataset | Path | Lines including header | Columns |
| --- | --- | ---: | --- |
| GC | `historical/data/gc.csv` | 15,142,967 | `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol` |
| SI | `historical/data/si.csv` | 9,830,594 | `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol` |

Chain facts:

| Root | Path | Multiplier | Tick Size | Timezone | Contracts |
| --- | --- | ---: | ---: | --- | ---: |
| GC | `historical/chains/GC.json` | 100.0 | 0.1 | `US/Eastern` | 224 |
| SI | `historical/chains/SI.json` | 5000.0 | 0.005 | `US/Eastern` | 230 |

Known spread-symbol rows appear in the first sample rows and must be classified
or excluded before outright futures backtests:

- GC sample: `GCN0-GCQ0`, `GCQ0-GCZ0`
- SI sample: `SIN0-SIZ0`

## Task Log

| Task | Status | Notes |
| --- | --- | --- |
| S5-00-T01 | Complete | Historical inventory recorded. |
| S5-01-T01 | Complete | `load_historical_chain` parses GC/SI metadata into typed chain/contract objects with `Decimal` tick size and multiplier. |
| S5-01-T02 | Complete | Outright historical symbols map to `InstrumentId`; spread symbols are rejected. |
| S5-02-T01 | Complete | CSV dataset descriptions read headers cheaply and count rows only when requested. |
| S5-02-T02 | Complete | CSV rows stream lazily into complete one-minute `Bar` objects; spread rows are excluded and counted. |
| S5-02-T03 | Complete | Generic historical catalog loader uses requested roots and symbol resolver boundaries without row counting by default. |
| S5-03-T01 | Complete | Sample validation reports invalid OHLC as errors and spread exclusions as visible info issues. |
| S5-03-T02 | Complete | `scripts/validate_historical.py --roots ...` writes JSON sample/full validation evidence; `make validate-historical-sample` added. |
| S5-04-T01 | Complete | `BacktestRunConfig` loads YAML, validates material run fields, and computes a stable config hash. |
| S5-04-T02 | Complete | `BacktestEngine.from_config` runs from full config and preserves existing constructor behavior. |
| S5-05-T01 | Complete | Backtest market data events order by end time, instrument ID, and source sequence. |
| S5-05-T02 | Complete | Warmup bars call strategies and update data/indicators while discarding trading intents. |
| S5-05-T03 | Complete | Strategy `finalize(ctx)` hook runs once and finalize intents are ignored. |
| S5-06-T01 | Complete | Backtest fills and portfolio views use configured futures contract multipliers; GC/SI multiplier anchors added. |
| S5-06-T02 | Complete | Fixed per-contract commission and basis-point slippage are explicit and reflected in fills/reports. |
| S5-07-T01 | Complete | Streaming artifacts serialize deterministic manifest, orders, fills, trade ledger, equity curve, metrics, and hash. |
| S5-07-T02 | Complete | Equity metrics include total return, max drawdown, and point count. |
| S5-07-T03 | Complete | Trade ledger rows are populated from idempotent validated fills. |
| S5-08-T01 | Complete | `StrategyContext.subscribe` records strategy data needs without exposing market data internals. |
| S5-08-T02 | Complete | Indicator warmup updates from completed visible bars before strategy callbacks. |
| S5-09-T01 | Complete | `run_backtest` and CLI run config-driven fixture and historical GC/SI backtests and write report JSON. |
| S5-09-T02 | Complete | `examples/strategies/gc_si_momentum.py` uses only Strategy SDK and standard library imports. |
| S5-10-T01 | Complete | Backtest replay determinism test and `make test-backtest-replay` added. |
| S5-10-T02 | Complete | `backtest-full-smoke` Make target is explicit and CLI writes elapsed/row/bar/spread/report summary evidence. |
| S5-10-T03 | Complete | Storage benchmark recorded in `docs/decision/2026-05-10_research_storage_decision.md`; no new dependency added for S5. |
| S5-11-T01 | Complete | Continuous futures roll selection uses shared `FutureRollRegistry`; historical GC/SI root runs select one concrete contract per timestamp and roll positions through the backtest order path. |

Focused verification:

```text
uv run pytest tests/unit/data/test_historical_chains.py tests/unit/data/test_historical_csv_dataset.py tests/integration/test_gc_si_historical_loading.py
12 passed
```

Final verification:

```text
make validate-historical-sample
evidence/historical/historical_validation_sample_1000.json

make test-backtest-replay
1 passed

make test-soak
2 passed

make test-reconciliation
1 passed

make backtest-full-smoke
report: runs/backtests/full-smoke/bt-6c6b18bf51f4.json
summary: runs/backtests/full-smoke/bt-6c6b18bf51f4.summary.json
elapsed_seconds=0.008212
processed_rows=26
emitted_bars=10
excluded_spreads=5
contracts_excluded=5
processed_bars=10
report_hash=sha256:ca24c027a541423aed5bb32637c21c4b671027e389bbdb8d3df7d3abf40a706f

make check
format: 302 files left unchanged
lint: All checks passed
mypy: Success, no issues in 286 source files
unit: 190 passed
integration: 35 passed
anchor: 23 passed
```

Storage decision:

- Bounded CSV streaming benchmark: 0.000205s, 0.016 MB RSS delta.
- Current JSONL write/read benchmark: 0.001068s write, 0.001007s read, 5,807 bytes.
- Decision: keep CSV streaming for S5; no `pyarrow` dependency without larger-run evidence.
