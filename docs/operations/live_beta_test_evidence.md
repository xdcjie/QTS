# Live Beta Test Evidence

Date: 2026-05-10

Latest pre-implementation baseline:

- `make check`: passed.
- Unit tests: 118 passed.
- Integration tests: 16 passed.
- Anchor tests: 17 passed.

Latest S3-specific focused check:

- `uv run pytest tests/unit/execution/test_live_broker_contract.py tests/unit/data/test_live_feed_contract.py tests/unit/reconciliation/test_reconciliation.py tests/unit/runtime/test_live_runtime.py tests/unit/risk/test_kill_switch.py tests/unit/runtime/test_account_partitioning.py tests/unit/api/test_operational_api_models.py tests/unit/observability/test_metrics.py tests/unit/load/test_synthetic_market_data.py tests/integration/test_live_beta_flows.py tests/anchor/test_live_beta_boundaries.py`
- Result: 21 passed after adding idempotent bootstrap coverage.

Final S3 verification:

- `make check`: passed.
- Mypy: success, no issues in 251 source files.
- Unit tests: 133 passed.
- Integration tests: 20 passed.
- Anchor tests: 19 passed.

Frontend verification:

- `npm run build`: passed.
