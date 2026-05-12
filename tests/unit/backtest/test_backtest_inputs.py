from __future__ import annotations

import csv
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.backtest.config import BacktestRunConfig, RiskConfig
from qts.core.ids import InstrumentId
from qts.data.historical.catalog import (
    HistoricalCatalog,
    HistoricalCatalogLoadConfig,
)
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS


def test_backtest_input_builder_creates_streaming_inputs_from_configured_dataset(
    tmp_path: Path,
) -> None:
    from qts.backtest.inputs import BacktestInputBuilder

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    _write_fixture_csv(historical_root / "data" / "equity.csv")
    config = BacktestRunConfig(
        dataset_root=historical_root,
        roots=("EQUITY",),
        symbols=("AAPL",),
        instrument_ids={"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")},
        start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
        end=datetime(2010, 6, 6, 22, 1, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("100000"),
        strategy_class="tests.integration.test_backtest_gc_si:BuyOneAaplStrategy",
        risk_config=RiskConfig(max_notional=Decimal("100000000")),
    )

    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_legacy_root(
            historical_root,
            roots=config.roots,
            instrument_ids=config.instrument_ids,
            requested_timeframe=config.timeframe,
        )
    )
    inputs = BacktestInputBuilder(config, catalog).build()
    bars = list(inputs.bars)

    assert [bar.instrument_id for bar in bars] == [InstrumentId("EQUITY.US.NASDAQ.AAPL")]
    assert inputs.dataset_stats["EQUITY"]["bars_emitted"] == 1
    assert inputs.dataset_metadata[0].instrument_id == InstrumentId("DATASET.EQUITY")
    assert inputs.instrument_registry.resolve("AAPL") == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert inputs.future_roll_registry is None
    assert inputs.exchange_timezone_by_instrument == {}


def _write_fixture_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "ts_event": "2010-06-06T22:00:00.000000000Z",
                "rtype": "33",
                "publisher_id": "1",
                "instrument_id": "AAPL",
                "open": "150.0",
                "high": "150.0",
                "low": "150.0",
                "close": "150.0",
                "volume": "100",
                "symbol": "AAPL",
            }
        )
