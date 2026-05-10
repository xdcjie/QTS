.PHONY: install format lint typecheck test-unit test-integration test-anchor test quick-check check load-test soak-test

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

test:
	uv run pytest

quick-check: format lint typecheck test-unit

check: format lint typecheck test-unit test-integration test-anchor

load-test:
	PYTHONPATH=backend/src uv run python scripts/run_load.py

soak-test:
	@echo "Manual soak gate: run paper trading for the duration documented in docs/operations/load_and_soak.md"
