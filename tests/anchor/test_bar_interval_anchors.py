from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal


def test_bar_interval_is_half_open_and_has_no_single_timestamp_identity() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    end = start + timedelta(minutes=1)
    bar = Bar(
        instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
        start_time=start,
        end_time=end,
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("2350.10"),
        high=Decimal("2351.00"),
        low=Decimal("2349.80"),
        close=Decimal("2350.50"),
        volume=Decimal("42"),
    )

    assert bar.interval.contains(start)
    assert not bar.interval.contains(end)
    assert not hasattr(bar, "timestamp")
