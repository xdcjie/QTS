.PHONY: install format lint guardrails typecheck test-unit test-integration test-anchor test-replay test-backtest-replay test-reconciliation test-soak test quick-check check load-test soak-test readiness-check validate-historical-sample backtest-full-smoke backtest-acceptance backtest-gc-full

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check .

guardrails:
	uv run python scripts/verify_guardrails.py

typecheck:
	uv run mypy backend tests

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

test-anchor:
	uv run pytest tests/anchor

test-replay:
	uv run pytest tests/replay

test-backtest-replay:
	uv run pytest tests/replay/test_backtest_determinism.py

test-reconciliation:
	uv run pytest tests/reconciliation

test-soak:
	uv run pytest tests/soak

test:
	uv run pytest

quick-check: format lint guardrails typecheck test-unit

check: format lint guardrails typecheck test-unit test-integration test-anchor

load-test:
	PYTHONPATH=backend/src uv run python scripts/run_load.py

soak-test:
	@echo "Manual soak gate: run paper trading for the duration documented in docs/operations/load_and_soak.md"

readiness-check: check test-replay test-reconciliation test-soak

validate-historical-sample:
	PYTHONPATH=backend/src uv run python scripts/validate_historical.py --root historical --roots GC SI --sample-rows 1000

backtest-full-smoke:
	PYTHONPATH=backend/src uv run python scripts/run_backtest.py --config configs/backtest.gc_si.example.yaml --output-dir runs/backtests/full-smoke

backtest-acceptance:
	PYTHONPATH=backend/src uv run python scripts/validate_historical.py --root historical --roots GC --sample-rows 1000 --output-dir evidence/historical
	PYTHONPATH=backend/src uv run pytest tests/unit/data/test_historical_data_config.py tests/unit/data/test_historical_csv_dataset.py tests/unit/data/test_historical_chains.py tests/unit/runtime/test_market_data_actor.py tests/unit/strategy_sdk/test_data_view.py tests/integration/test_backtest_gc_si.py tests/integration/test_backtest_engine_flow.py tests/anchor tests/replay/test_backtest_determinism.py tests/replay/test_backtest_report_hash.py
	PYTHONPATH=backend/src uv run python scripts/run_backtest.py --config configs/backtest.gc_si.example.yaml --output-dir runs/backtests/stage-acceptance

backtest-gc-full:
	@test "$$QTS_CONFIRM_FULL_GC" = "1" || (echo "Set QTS_CONFIRM_FULL_GC=1 to run the current full GC backtest path."; exit 2)
	PYTHONPATH=backend/src uv run python scripts/run_backtest.py --config configs/backtest.gc.full.example.yaml --output-dir runs/backtests/gc-full
