"""Catalog futures economics flow into the backtest margin policy."""

from __future__ import annotations

import csv
import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.backtest.risk_policy import BacktestMarginPolicyResolver
from qts.core.ids import InstrumentId
from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
from qts.data.sources.replay_bundle_builder import ReplayMarketDataBundleBuilder
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
    RollPolicyConfig,
)


def test_catalog_futures_margin_rate_flows_into_backtest_margin_policy(tmp_path: Path) -> None:
    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), historical_root / "chains" / "GC.json")
    csv_path = historical_root / "data" / "gc.csv"
    _write_future_rows(csv_path, [("2010-06-06T22:00:00.000000000Z", "GCQ0", "1200.0")])
    data_config_path = tmp_path / "historical.local.yaml"
    data_config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
      defaults:
        exchange_timezone: US/Eastern
        timezone_policy: source_utc_exchange_sessions
        normalization: raw
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          chain_file: GC.json
          bars:
            - file: gc.csv
              timeframe: 1m
""",
        encoding="utf-8",
    )
    config = BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            config_path=data_config_path,
            catalog="research_futures",
        ),
        roots=("GC",),
        symbols=("GCM0",),
        start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
        end=datetime(2010, 6, 6, 22, 2, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("1000000"),
        strategy_class="tests.integration.test_catalog_futures_margin_enforced:Noop",
        roll_policy=RollPolicyConfig(enabled=False),
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
    )
    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            data_config_path,
            catalog="research_futures",
            roots=config.roots,
            instrument_ids=config.instrument_ids,
            requested_timeframe=config.timeframe,
        )
    )

    bundle = ReplayMarketDataBundleBuilder(config=config, catalog=catalog).build()
    contract = bundle.instrument_registry.get_instrument(InstrumentId("FUTURE.CME.GC.GCQ0"))

    assert contract.contract_spec.initial_margin_rate == Decimal("0.10")
    assert BacktestMarginPolicyResolver().resolve_initial_margin_rate(
        bundle.instrument_registry
    ) == Decimal("0.10")


def _write_future_rows(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for index, (ts_event, symbol, close) in enumerate(rows, start=1):
            writer.writerow(
                {
                    "ts_event": ts_event,
                    "rtype": "33",
                    "publisher_id": "1",
                    "instrument_id": str(index),
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": "100",
                    "symbol": symbol,
                }
            )
