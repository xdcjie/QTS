from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal


def test_bar_carries_explicit_timeframe_session_and_completion_state() -> None:
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
        is_complete=True,
        is_partial=False,
    )

    assert bar.timeframe == "1m"
    assert bar.session_id == "2026-01-02"
    assert bar.is_complete
    assert not bar.is_partial
