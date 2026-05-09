from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def _bar(start: datetime, close: str = "100") -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_in_memory_market_data_store_reads_sorted_half_open_ranges() -> None:
    from qts.data.stores import InMemoryMarketDataStore

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    store = InMemoryMarketDataStore()
    store.write_bars([_bar(start + timedelta(minutes=1), "101"), _bar(start, "100")])

    result = store.read_bars(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        timeframe="1m",
        start=start,
        end=start + timedelta(minutes=1),
    )

    assert [bar.close for bar in result] == [Decimal("100")]


def test_parquet_market_data_store_round_trips_without_vendor_symbols(tmp_path: Path) -> None:
    from qts.data.stores import ParquetMarketDataStore

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    store = ParquetMarketDataStore(tmp_path)
    bars = (_bar(start, "100"), _bar(start + timedelta(minutes=1), "101"))

    store.write_bars(bars)

    assert (
        store.read_bars(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            timeframe="1m",
            start=start,
            end=start + timedelta(minutes=2),
        )
        == bars
    )


def test_replay_feed_preserves_deterministic_bar_events() -> None:
    from qts.data.feeds import ReplayFeed
    from qts.data.stores import InMemoryMarketDataStore

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    store = InMemoryMarketDataStore()
    store.write_bars([_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")])

    first = ReplayFeed(store).events(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        timeframe="1m",
        start=start,
        end=start + timedelta(minutes=2),
    )
    second = ReplayFeed(store).events(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        timeframe="1m",
        start=start,
        end=start + timedelta(minutes=2),
    )

    assert first == second
    assert all(isinstance(event.payload, Bar) for event in first)
    assert [event.payload.timeframe for event in first if isinstance(event.payload, Bar)] == [
        "1m",
        "1m",
    ]
