from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.registry.calendar_registry import MarketSession


@dataclass(frozen=True)
class _FakeCalendarRegistry:
    session: MarketSession

    def session_for(self, calendar_id: str, session_date: date) -> MarketSession:
        assert calendar_id == "XNYS"
        assert session_date == date(2026, 1, 2)
        return self.session


from qts.core.ids import InstrumentId
from qts.core.time import TimeInterval
from qts.data.sessions.filter import filter_session_bars


def _bar(start: datetime, end: datetime) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=end,
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.50"),
        volume=Decimal("1000"),
    )


def test_session_filter_includes_inside_bars_and_excludes_close_boundary() -> None:
    open_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    close_time = datetime(2026, 1, 2, 21, 0, tzinfo=UTC)
    session = MarketSession(
        calendar_id="XNYS",
        session_id="2026-01-02",
        interval=TimeInterval(start=open_time, end=close_time),
    )
    inside = _bar(open_time, open_time + timedelta(minutes=1))
    at_close = _bar(close_time, close_time + timedelta(minutes=1))
    outside = _bar(open_time - timedelta(minutes=1), open_time)

    filtered = filter_session_bars(
        [outside, inside, at_close],
        calendar_registry=_FakeCalendarRegistry(session),
        calendar_id="XNYS",
        session_date=date(2026, 1, 2),
    )

    assert filtered == [inside]
