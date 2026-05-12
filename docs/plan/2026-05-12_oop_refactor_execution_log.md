# OOP Refactor Baseline Execution Log (2026-05-12)

Date: 2026-05-12 17:36:32 CST

## OOP-00-T01 Command Runbook

Executed from repository root (`/Users/bjhl/Projects/QTS`) in order:

1) `make format`

- Result: passed (formatter reported 3 files reformatted, 356 unchanged)
- Reformatted files:
  - `backend/src/qts/backtest/engine.py`
  - `backend/src/qts/backtest/report.py`
  - `backend/src/qts/data/live_feed.py`

2) `make lint`

- Result: passed

3) `make guardrails`

- Result: passed

4) `make typecheck`

- Result: failed with existing pre-existing type issues (no refactor work introduced yet in this task)
- Failures:
  - `tests/unit/runtime/test_router.py`
    - line 44: `"object"` has no attribute `account_id`
    - line 57: `"object"` has no attribute `account_id`
    - line 81: `"object"` has no attribute `market_data_source_id`
    - line 82: `"object"` has no attribute `account_id`
  - `tests/unit/backtest/test_backtest_runner.py`
    - line 27: Function is missing type annotations
    - line 48: `Strategy` has no attribute `note`
    - line 66: Function is missing type annotations

5) `make test-unit`

- Result: passed
- Tests passed: 275

## Notes

- `OOP-00-T01` requirement satisfied: baseline captured before refactor steps.
- Command results include existing failures separately so future refactor regressions can be distinguished.
