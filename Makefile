.PHONY: install format lint typecheck test-unit test-integration test-anchor test-replay test-research-replay test-reconciliation test-soak test quick-check check load-test soak-test readiness-check validate-historical-sample research-full-smoke

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check .

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

test-research-replay:
	uv run pytest tests/replay/test_research_backtest_determinism.py

test-reconciliation:
	uv run pytest tests/reconciliation

test-soak:
	uv run pytest tests/soak

test:
	uv run pytest

quick-check: format lint typecheck test-unit

check: format lint typecheck test-unit test-integration test-anchor

load-test:
	PYTHONPATH=backend/src uv run python scripts/run_load.py

soak-test:
	@echo "Manual soak gate: run paper trading for the duration documented in docs/operations/load_and_soak.md"

readiness-check: check test-replay test-reconciliation test-soak

validate-historical-sample:
	PYTHONPATH=backend/src uv run python scripts/validate_historical_gc_si.py --root historical --sample-rows 1000

research-full-smoke:
	PYTHONPATH=backend/src uv run python scripts/run_research_backtest.py --config configs/backtest.gc_si.example.yaml --output-dir runs/backtests/full-smoke
