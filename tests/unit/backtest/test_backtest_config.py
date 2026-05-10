from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.backtest.config import BacktestRunConfig


def test_backtest_run_config_loads_example_yaml_with_stable_hash() -> None:
    config = BacktestRunConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))

    assert config.dataset_root == Path("historical")
    assert config.roots == ("GC", "SI")
    assert config.symbols == ("GCQ0", "SIN0")
    assert config.start == datetime(2010, 6, 6, 22, 0, tzinfo=UTC)
    assert config.end == datetime(2010, 6, 6, 22, 5, tzinfo=UTC)
    assert config.timeframe == "1m"
    assert config.initial_cash == Decimal("1000000")
    assert config.strategy_class == "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
    assert config.strategy_params == {"symbols": ["GCQ0", "SIN0"]}
    assert config.cost_model.fixed_commission_per_contract == Decimal("0")
    assert config.cost_model.slippage_bps == Decimal("0")
    assert config.risk_config.max_notional == Decimal("100000000")
    assert (
        config.config_hash
        == BacktestRunConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml")).config_hash
    )

    changed = replace(config, initial_cash=Decimal("2000000"))
    assert changed.config_hash != config.config_hash


def test_backtest_run_config_validates_material_fields() -> None:
    config = BacktestRunConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))

    with pytest.raises(ValueError, match="roots"):
        replace(config, roots=())
    with pytest.raises(ValueError, match="date range"):
        replace(config, start=config.end, end=config.start)
    with pytest.raises(ValueError, match="initial_cash"):
        replace(config, initial_cash=Decimal("0"))
