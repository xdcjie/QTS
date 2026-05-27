from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml  # type: ignore[import-untyped]


def test_removed_vwap_pullback_module_is_not_available() -> None:
    assert not Path("examples/strategies/vwap_pullback.py").exists()
    assert importlib.util.find_spec("examples.strategies.vwap_pullback") is None


def test_backtest_loader_uses_v2_vwap_strategy_path() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    from examples.strategies.vwap_pullback_v2 import VwapPullbackV2Strategy

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.vwap_pullback_v2:VwapPullbackV2Strategy",
        {"symbol": "GC"},
    )

    assert isinstance(strategy, VwapPullbackV2Strategy)


def test_vwap_strategy_config_points_to_v2_strategy() -> None:
    payload = yaml.safe_load(Path("configs/strategies/vwap_pullback.yaml").read_text())

    assert payload["class_path"] == "examples.strategies.vwap_pullback_v2:VwapPullbackV2Strategy"
    assert payload["params"] == {"symbol": "GC"}
