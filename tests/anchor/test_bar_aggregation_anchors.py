from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal


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
