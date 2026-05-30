"""QTS-FINAL-015: BacktestPipeline delegates strategy loading to StrategyLoader.

The pipeline is a facade; the dynamic-import strategy-loading concern lives in
``StrategyLoader`` (and the pipeline module no longer imports importlib/sys).
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.backtest.pipeline import BacktestPipeline
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)
from qts.strategy_sdk import Strategy
from qts.strategy_sdk.loading import StrategyLoader

from tests.support.loader_demo_strategy import DemoStrategy

_DEMO = "tests.support.loader_demo_strategy"


def test_strategy_loader_loads_by_colon_and_dot_paths() -> None:
    loader = StrategyLoader()
    colon = loader.load(f"{_DEMO}:DemoStrategy", {"window": 3})
    dotted = loader.load(f"{_DEMO}.DemoStrategy", {})
    assert isinstance(colon, DemoStrategy)
    assert colon.params == {"window": 3}
    assert isinstance(dotted, DemoStrategy)


def test_strategy_loader_rejects_malformed_and_missing() -> None:
    loader = StrategyLoader()
    import pytest

    with pytest.raises(ValueError, match="module:Class"):
        loader.load("nodelimiter", {})
    with pytest.raises(ValueError, match="not found"):
        loader.load(f"{_DEMO}:NoSuchStrategy", {})


def test_pipeline_module_does_not_import_dynamic_loading_machinery() -> None:
    source = Path("backend/src/qts/backtest/pipeline.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0])
    assert "importlib" not in roots
    assert "sys" not in roots


def test_pipeline_load_strategy_set_uses_loader_for_configured_strategies() -> None:
    config = BacktestRuntimeConfig(
        roots=("AAPL",),
        symbols=("AAPL",),
        start=datetime(2026, 1, 2, tzinfo=UTC),
        end=datetime(2026, 1, 3, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("10000"),
        strategy_class=f"{_DEMO}:DemoStrategy",
        strategy_params={"window": 5},
        market_data=BacktestMarketDataReference(config_path=Path("md.yaml"), catalog="research"),
        risk_config=BacktestRiskConfig(max_notional=Decimal("1000000")),
    )
    strategies = BacktestPipeline(config).load_strategy_set()
    assert len(strategies) == 1
    assert isinstance(strategies[0], Strategy)
    assert isinstance(strategies[0], DemoStrategy)
    assert strategies[0].params == {"window": 5}
