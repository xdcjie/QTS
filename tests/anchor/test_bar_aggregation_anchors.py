from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.domain.market_data import Bar


def test_ohlcv_aggregation_uses_first_max_min_last_sum_rules() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.bars.aggregator import aggregate_bars
    from qts.data.bars.timeframe import Timeframe
    from qts.domain.market_data import Bar

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [
        Bar(
            instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
            start_time=start + timedelta(minutes=offset),
            end_time=start + timedelta(minutes=offset + 1),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal(open_price),
            high=Decimal(high),
            low=Decimal(low),
            close=Decimal(close),
            volume=Decimal(volume),
            is_complete=True,
        )
        for offset, open_price, high, low, close, volume in [
            (0, "10", "11", "9", "10.5", "1"),
            (1, "10.5", "12", "10", "11", "2"),
            (2, "11", "11.5", "8", "9", "3"),
            (3, "9", "10", "8.5", "9.5", "4"),
            (4, "9.5", "10.5", "9", "10", "5"),
        ]
    ]

    [aggregated] = aggregate_bars(
        bars,
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=UTC,
    )

    assert aggregated.open == Decimal("10")
    assert aggregated.high == Decimal("12")
    assert aggregated.low == Decimal("8")
    assert aggregated.close == Decimal("10")
    assert aggregated.volume == Decimal("15")


def test_gc_2026_05_20_replay_aggregates_one_minute_source_to_daily_anchor() -> None:
    from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
    from qts.data.sources.replay_bundle_builder import ReplayMarketDataBundleBuilder
    from qts.runtime.config import (
        BacktestMarketDataReference,
        BacktestRiskConfig,
        BacktestRuntimeConfig,
        RollPolicyConfig,
    )
    from qts.runtime.market_data_flow import MarketDataFlow

    session_start = datetime(2026, 5, 19, 22, 0, tzinfo=UTC)
    session_end = datetime(2026, 5, 20, 21, 0, tzinfo=UTC)
    config = BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            config_path=Path("configs/data/historical.local.yaml"),
            catalog="research_futures",
        ),
        roots=("GC",),
        symbols=("GC",),
        start=session_start,
        end=session_end,
        timeframe="1d",
        initial_cash=Decimal("1000000"),
        strategy_class="tests.integration.test_backtest_gc_si:RollingGcStrategy",
        roll_policy=RollPolicyConfig(enabled=True),
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
    )
    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            Path("configs/data/historical.local.yaml"),
            catalog="research_futures",
            roots=config.roots,
            instrument_ids=config.instrument_ids,
            requested_timeframe=config.timeframe,
        )
    )
    bundle = ReplayMarketDataBundleBuilder(config=config, catalog=catalog).build()
    flow = MarketDataFlow(
        target_timeframe="1d",
        exchange_timezone_by_instrument=bundle.exchange_timezone_by_instrument,
        session_window_by_instrument=bundle.session_window_by_instrument,
    )

    emitted: list[Bar] = []
    for source_bar in bundle.bars:
        emitted.extend(flow.publish_bar(source_bar))

    assert len(emitted) == 1
    [daily] = emitted
    assert daily.instrument_id.value == "CONTINUOUS_FUTURE.CME.GC"
    assert daily.start_time == session_start
    assert daily.end_time == session_end
    assert daily.timeframe == "1d"
    assert daily.session_id == "2026-05-20"
    assert daily.open == Decimal("4486.600000000")
    assert daily.high == Decimal("4558.400000000")
    assert daily.low == Decimal("4455.000000000")
    assert daily.close == Decimal("4546.200000000")
    assert daily.volume == Decimal("109695")
    assert daily.is_complete
    assert not daily.is_partial
