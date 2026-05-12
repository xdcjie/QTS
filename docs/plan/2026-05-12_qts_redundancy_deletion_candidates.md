# 2026-05-12 — Redundancy and Deletion Candidate Register

This register lists code that should be reviewed for deletion, consolidation, or extraction. It is not an instruction to delete immediately.

## A. Empty non-`__init__` modules

| File | Signal | Action |
|---|---|---|
| `backend/src/qts/data/bars/builder.py` | 0 symbols | Delete if unimported, or implement cohesive `BarBuilder`. |
| `backend/src/qts/data/bars/validation.py` | 0 symbols | Delete if unimported, or implement bar validation module. |
| `scripts/run_api.py` | 0 symbols | Implement thin `main()` or delete if not documented. |
| `scripts/run_paper_ibkr.py` | 0 symbols | Implement thin `main()` or delete if not documented. |
| `scripts/run_worker.py` | 0 symbols | Implement thin `main()` or delete if not documented. |

Required check:

```bash
rg "data\.bars\.builder|BarBuilder|data\.bars\.validation|validate_bar|run_api|run_paper_ibkr|run_worker"
make test-unit
make test-integration
make test-anchor
```

## B. Duplicate helper concepts

| Concept | Current locations | Target |
|---|---|---|
| stable JSON hash | `backtest.report._stable_hash`, `BacktestRunConfig._stable_hash`, `BacktestEngine._stable_hash` | `qts.core.hashing.stable_json_hash` |
| IBKR config validation | `scripts/ibkr_*` helpers and `qts.config.ibkr.validate_ibkr_environment` | central config validator |
| instrument symbol/exchange parsing | `BacktestEngine._symbol_for`, `_exchange_for` | registry/instrument metadata |
| artifact sink logic | nested in `BacktestEngine` and report writer | `qts.backtest.sinks` / report layer |

## C. Extract-not-delete candidates

| Symbol/area | Why not delete | Target action |
|---|---|---|
| `BacktestEngine._StreamingBacktestSink` | used by engine, but wrong owner | move to `qts.backtest.sinks` |
| `BacktestEngine._ProcessedIntent` | internal data holder | move near intent processor or keep private after split |
| `BacktestEngine._RuntimeRunResult` | result value object | move to actor loop module |
| application DTOs vs API schemas | boundary separation may be intentional | add mapper layer; delete only verified orphans |
| FastAPI route functions | static inventory may not see framework calls | keep unless route removed intentionally |
| Protocol methods | often have no static caller | keep if part of interface |

## D. Final deletion gate

A symbol/file may be deleted only when:

- no direct import or string reference exists;
- not a framework route, CLI entrypoint, plugin hook, callback, or public API;
- tests pass before and after deletion;
- if public, migration/deprecation decision is documented;
- GoalAgent diff and architecture gates pass.
