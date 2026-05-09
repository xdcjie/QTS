.PHONY: install format lint typecheck test-unit test-integration test-anchor test quick-check check

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
