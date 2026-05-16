from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.core.ids import InstrumentId
from qts.runtime.config import BacktestRuntimeConfig, ConfigMigration
from qts.runtime.config_loader import BacktestConfigLoader


def test_backtest_run_config_loads_example_yaml_with_stable_hash() -> None:
    config = BacktestRuntimeConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))

    assert config.market_data.config_path == Path("configs/data/historical.local.yaml")
    assert config.market_data.catalog == "research_futures"
    assert not hasattr(config, "historical_data")
    assert not hasattr(config, "dataset_root")
    assert config.roots == ("GC", "SI")
    assert config.symbols == ("GC", "SI")
    assert config.instrument_ids == {}
    assert config.roll_policy.enabled is True
    assert config.start == datetime(2010, 6, 6, 22, 0, tzinfo=UTC)
    assert config.end == datetime(2010, 6, 6, 22, 5, tzinfo=UTC)
    assert config.timeframe == "1m"
    assert config.initial_cash == Decimal("1000000")
    assert config.strategy_config_path == Path("configs/strategies/gc_si_momentum.yaml")
    assert config.strategy_class == "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
    assert config.strategy_params == {"symbols": ["GC", "SI"]}
    assert config.cost_model.fixed_commission_per_contract == Decimal("0")
    assert config.cost_model.slippage_bps == Decimal("0")
    assert config.risk_config.max_notional == Decimal("100000000")
    assert (
        config.config_hash
        == BacktestRuntimeConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml")).config_hash
    )

    changed = replace(config, initial_cash=Decimal("2000000"))
    assert changed.config_hash != config.config_hash


def test_backtest_config_schema_version_is_part_of_config_hash() -> None:
    config = BacktestRuntimeConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))

    changed = replace(config, schema_version="2")

    assert config.schema_version == "1"
    assert config.to_payload()["schema_version"] == "1"
    assert config.to_payload()["risk_config"]["schema_version"] == "1"
    assert changed.config_hash != config.config_hash


def test_config_migration_v1_to_v2_adds_schema_versions_and_changelog() -> None:
    payload = {
        "schema_version": "1",
        "risk_config": {"max_notional": "100000"},
    }

    result = ConfigMigration.migrate(payload, target_version="2")

    assert payload["schema_version"] == "1"
    assert result.from_version == "1"
    assert result.to_version == "2"
    assert result.payload["schema_version"] == "2"
    assert result.payload["risk_config"]["schema_version"] == "2"
    assert result.change_log == (
        "schema_version: 1 -> 2",
        "risk_config.schema_version: 1 -> 2",
    )


def test_backtest_loader_consumes_migrated_config_schema_version() -> None:
    payload = {
        "schema_version": "1",
        "market_data": {
            "source": "local_historical",
            "config": "configs/data/historical.local.yaml",
            "catalog": "research_futures",
        },
        "roots": ["GC"],
        "symbols": ["GC"],
        "start": "2026-01-02T14:30:00Z",
        "end": "2026-01-02T14:31:00Z",
        "timeframe": "1m",
        "initial_cash": "100000",
        "strategy_class": "tests.integration.test_backtest_gc_si:RollingGcStrategy",
        "risk_config": {"max_notional": "100000"},
    }

    migrated = ConfigMigration.migrate(payload, target_version="2")
    config = BacktestConfigLoader.from_payload(migrated.payload)

    assert config.schema_version == "2"
    assert config.risk_config.schema_version == "2"
    assert config.to_payload()["schema_version"] == "2"
    assert config.to_payload()["risk_config"]["schema_version"] == "2"


def test_backtest_run_config_loads_gc_full_example_yaml() -> None:
    config = BacktestRuntimeConfig.from_yaml(Path("configs/backtest.gc.full.example.yaml"))

    assert config.market_data.config_path == Path("configs/data/historical.local.yaml")
    assert config.market_data.catalog == "research_futures"
    assert not hasattr(config, "dataset_root")
    assert config.roots == ("GC",)
    assert config.symbols == ("GC",)
    assert config.roll_policy.enabled is True
    assert config.roll_policy.method == "highest_volume"
    assert config.start == datetime(2010, 6, 6, 22, 0, tzinfo=UTC)
    assert config.end == datetime(2026, 4, 10, 0, 0, tzinfo=UTC)
    assert config.timeframe == "1m"
    assert config.strategy_config_path == Path("configs/strategies/gc_momentum.yaml")
    assert config.strategy_class == "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
    assert config.strategy_params == {
        "symbols": ["GC"],
        "short_window": 1,
        "long_window": 2,
    }


def test_backtest_run_config_can_reference_project_historical_catalog(tmp_path: Path) -> None:
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        """
market_data:
  source: local_historical
  config: configs/data/historical.local.yaml
  catalog: research_futures
roots: [GC]
symbols: [GC]
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_backtest_gc_si:RollingGcStrategy"
""",
        encoding="utf-8",
    )

    config = BacktestRuntimeConfig.from_yaml(config_path)

    assert config.market_data.source == "local_historical"
    assert config.market_data.config_path == Path("configs/data/historical.local.yaml")
    assert config.market_data.catalog == "research_futures"
    assert not hasattr(config, "historical_data")
    assert not hasattr(config, "dataset_root")


def test_backtest_run_config_rejects_obsolete_historical_data_alias(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        """
historical_data:
  source: local_historical
  config: configs/data/historical.local.yaml
  catalog: research_futures
roots: [GC]
symbols: [GC]
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_backtest_gc_si:RollingGcStrategy"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="backtest run configs must use market_data"):
        BacktestRuntimeConfig.from_yaml(config_path)


def test_backtest_run_config_rejects_obsolete_dataset_root(
    tmp_path: Path,
) -> None:
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
strategy_class: "tests.integration.test_backtest_gc_si:RollingGcStrategy"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="backtest run configs must use market_data"):
        BacktestRuntimeConfig.from_yaml(config_path)


def test_backtest_run_config_rejects_unsupported_market_data_source(tmp_path: Path) -> None:
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        """
market_data:
  source: live_gateway
  config: configs/data/historical.local.yaml
  catalog: research_futures
roots: [GC]
symbols: [GC]
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_backtest_gc_si:RollingGcStrategy"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported market_data.source"):
        BacktestRuntimeConfig.from_yaml(config_path)


def test_backtest_run_config_can_reference_strategy_config(tmp_path: Path) -> None:
    strategy_path = tmp_path / "strategies" / "gc_si_momentum.yaml"
    strategy_path.parent.mkdir()
    strategy_path.write_text(
        """
strategy_id: gc-si-momentum
class_path: examples.strategies.gc_si_momentum:GcSiMomentumStrategy
account_id: backtest-account
allocation: "1.0"
enabled: true
params:
  symbols: [GC, SI]
  short_window: 1
  long_window: 2
""",
        encoding="utf-8",
    )
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: configs/data/historical.local.yaml
  catalog: research_futures
roots: [GC, SI]
symbols: [GC, SI]
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_config: {strategy_path}
""",
        encoding="utf-8",
    )

    config = BacktestRuntimeConfig.from_yaml(config_path)

    assert config.market_data.source == "local_historical"
    assert config.strategy_config_path == strategy_path
    assert config.strategy_class == "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
    assert config.strategy_params == {
        "symbols": ["GC", "SI"],
        "short_window": 1,
        "long_window": 2,
    }


def test_backtest_run_config_accepts_explicit_instrument_ids_for_non_chain_datasets(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        """
market_data:
  source: local_historical
  config: configs/data/historical.local.yaml
  catalog: research_futures
roots: [EQUITY]
symbols: [AAPL]
instrument_ids:
  AAPL: EQUITY.US.NASDAQ.AAPL
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_backtest_gc_si:BuyOneGcStrategy"
""",
        encoding="utf-8",
    )

    config = BacktestRuntimeConfig.from_yaml(config_path)

    assert config.instrument_ids == {"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")}


def test_backtest_run_config_accepts_roll_policy(tmp_path: Path) -> None:
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text(
        """
market_data:
  source: local_historical
  config: configs/data/historical.local.yaml
  catalog: research_futures
roots: [GC]
symbols: [GC]
start: "2026-01-02T14:30:00Z"
end: "2026-01-02T14:31:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_backtest_gc_si:RollingGcStrategy"
roll_policy:
  enabled: true
  method: highest_volume
""",
        encoding="utf-8",
    )

    config = BacktestRuntimeConfig.from_yaml(config_path)

    assert config.roll_policy.enabled is True
    assert config.roll_policy.method == "highest_volume"


def test_backtest_run_config_validates_material_fields() -> None:
    config = BacktestRuntimeConfig.from_yaml(Path("configs/backtest.gc_si.example.yaml"))

    with pytest.raises(ValueError, match="roots"):
        replace(config, roots=())
    with pytest.raises(ValueError, match="date range"):
        replace(config, start=config.end, end=config.start)
    with pytest.raises(ValueError, match="initial_cash"):
        replace(config, initial_cash=Decimal("0"))
