from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.backtest.config import BacktestRunConfig
from qts.core.ids import InstrumentId


def test_backtest_run_config_loads_example_yaml_with_stable_hash() -> None:
    config = BacktestRunConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))

    assert config.dataset_root == Path("historical")
    assert config.roots == ("GC", "SI")
    assert config.symbols == ("GC", "SI")
    assert config.instrument_ids == {}
    assert config.roll_policy.enabled is True
    assert config.start == datetime(2010, 6, 6, 22, 0, tzinfo=UTC)
    assert config.end == datetime(2010, 6, 6, 22, 5, tzinfo=UTC)
    assert config.timeframe == "1m"
    assert config.initial_cash == Decimal("1000000")
    assert config.strategy_class == "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
    assert config.strategy_params == {"symbols": ["GC", "SI"]}
    assert config.cost_model.fixed_commission_per_contract == Decimal("0")
    assert config.cost_model.slippage_bps == Decimal("0")
    assert config.risk_config.max_notional == Decimal("100000000")
    assert (
        config.config_hash
        == BacktestRunConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml")).config_hash
    )

    changed = replace(config, initial_cash=Decimal("2000000"))
    assert changed.config_hash != config.config_hash


def test_backtest_run_config_accepts_explicit_instrument_ids_for_non_chain_datasets(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        """
dataset_root: historical
roots: [EQUITY]
symbols: [AAPL]
instrument_ids:
  AAPL: EQUITY.US.NASDAQ.AAPL
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_research_backtest_gc_si:BuyOneGcStrategy"
""",
        encoding="utf-8",
    )

    config = BacktestRunConfig.from_yaml(config_path)

    assert config.instrument_ids == {"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")}


def test_backtest_run_config_accepts_roll_policy(tmp_path: Path) -> None:
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        """
dataset_root: historical
roots: [GC]
symbols: [GC]
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_research_backtest_gc_si:RollingGcStrategy"
roll_policy:
  enabled: true
  method: highest_volume
""",
        encoding="utf-8",
    )

    config = BacktestRunConfig.from_yaml(config_path)

    assert config.roll_policy.enabled is True
    assert config.roll_policy.method == "highest_volume"


def test_backtest_run_config_validates_material_fields() -> None:
    config = BacktestRunConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))

    with pytest.raises(ValueError, match="roots"):
        replace(config, roots=())
    with pytest.raises(ValueError, match="date range"):
        replace(config, start=config.end, end=config.start)
    with pytest.raises(ValueError, match="initial_cash"):
        replace(config, initial_cash=Decimal("0"))
