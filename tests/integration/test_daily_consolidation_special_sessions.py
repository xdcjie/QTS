"""Integration: daily (1d) consolidation is calendar-aware over special sessions.

Domain fact: a ``1d`` bar covers exactly one trading session ``[open, close)``.
Holidays are not sessions; half-days close early. Daily consolidation must
derive each day's boundary from the calendar, not from a fixed clock window,
so a holiday is never treated as a full session and a half-day uses its
early close.

This exercises the production path:

    BarTimeGridSynthesizer (per-session 1m grid)
        -> NMinuteConsolidator(target=1d, session_window=CalendarSessionIntervalSource)

over a COMEX span (2024-12-23..2024-12-26) that contains a full session, a
half-day (Christmas Eve early close), a holiday (Christmas Day, absent), and
another full session.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.core.time import TimeInterval
from qts.data.bars.consolidator import NMinuteConsolidator
from qts.data.bars.time_grid_synthesizer import BarTimeGridSynthesizer
from qts.data.bars.timeframe import Timeframe
from qts.data.sessions import CalendarSessionIntervalSource, RegularSessionWindow
from qts.domain.market_data import Bar
from qts.registry.providers.exchange_calendar_provider import ExchangeCalendarProvider

_INSTRUMENT = InstrumentId("FUTURE.US.COMEX.GC")
_ONE_MINUTE = timedelta(minutes=1)
_CALENDAR = "COMEX"

# COMEX sessions for the test span (verified via exchange-calendars):
#   2024-12-23 full      [12-22 23:00, 12-23 23:00) UTC  -> 1440 minutes
#   2024-12-24 half-day  [12-23 23:00, 12-24 18:00) UTC  ->  half-day early close
#   2024-12-25 holiday   not a session                   ->  no daily bar
#   2024-12-26 full      [12-25 23:00, 12-26 23:00) UTC  -> 1440 minutes
_FULL_SESSION_1 = date(2024, 12, 23)
_HALF_DAY = date(2024, 12, 24)
_HOLIDAY = date(2024, 12, 25)
_FULL_SESSION_2 = date(2024, 12, 26)


def _tile_session(interval: TimeInterval, session_id: str) -> list[Bar]:
    """Return one real opening and closing one-minute bar for a session.

    The synthesizer fills every minute between them, producing a contiguous
    ``[open, close)`` grid for the session.
    """
    price = Decimal("2000.0")

    def bar(start: datetime) -> Bar:
        return Bar(
            instrument_id=_INSTRUMENT,
            start_time=start,
            end_time=start + _ONE_MINUTE,
            timeframe="1m",
            session_id=session_id,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=Decimal("1"),
            is_complete=True,
        )

    return [bar(interval.start), bar(interval.end - _ONE_MINUTE)]


def _consolidate_daily(provider: ExchangeCalendarProvider, session_dates: list[date]) -> list[Bar]:
    """Run the synthesizer -> daily consolidator path over the given sessions."""
    grid: list[Bar] = []
    synthesizer = BarTimeGridSynthesizer(timeframe="1m")
    for session_date in session_dates:
        interval = provider.session_interval_for(session_date)
        assert interval is not None, f"{session_date} unexpectedly resolved to no session"
        sparse = _tile_session(interval, session_date.isoformat())
        grid.extend(synthesizer.synthesize(iter(sparse)))

    consolidator = NMinuteConsolidator(
        source_timeframe=Timeframe.parse("1m"),
        target_timeframe=Timeframe.parse("1d"),
        exchange_timezone="America/New_York",
        session_window=CalendarSessionIntervalSource(provider),
    )
    emitted: list[Bar] = []
    for bar in grid:
        emitted.extend(consolidator.update(bar))
    return emitted


def test_daily_consolidation_over_holiday_and_half_day_uses_calendar_sessions() -> None:
    provider = ExchangeCalendarProvider(_CALENDAR)
    # The holiday is not a session, so upstream tags no bars to it; we feed only
    # the three real trading sessions in the span.
    daily = _consolidate_daily(
        provider,
        [_FULL_SESSION_1, _HALF_DAY, _FULL_SESSION_2],
    )

    by_session = {bar.session_id: bar for bar in daily}

    # Exactly one daily bar per trading session; the holiday produced none.
    assert set(by_session) == {
        _FULL_SESSION_1.isoformat(),
        _HALF_DAY.isoformat(),
        _FULL_SESSION_2.isoformat(),
    }
    assert _HOLIDAY.isoformat() not in by_session

    # Each daily bar tiles exactly its calendar session [open, close).
    for session_date in (_FULL_SESSION_1, _HALF_DAY, _FULL_SESSION_2):
        interval = provider.session_interval_for(session_date)
        assert interval is not None
        bar = by_session[session_date.isoformat()]
        assert bar.timeframe == "1d"
        assert bar.start_time == interval.start
        assert bar.end_time == interval.end
        assert bar.is_complete
        assert not bar.is_partial


def test_half_day_daily_bar_closes_early_not_full_session() -> None:
    provider = ExchangeCalendarProvider(_CALENDAR)
    daily = _consolidate_daily(provider, [_HALF_DAY])

    assert len(daily) == 1
    [half_day_bar] = daily

    half_interval = provider.session_interval_for(_HALF_DAY)
    full_interval = provider.session_interval_for(_FULL_SESSION_2)
    assert half_interval is not None and full_interval is not None

    # The half-day closes at the early calendar close (18:00 UTC), and its
    # session is strictly shorter than a full session.
    assert half_day_bar.end_time == half_interval.end
    assert half_interval.duration < full_interval.duration
    assert half_day_bar.end_time - half_day_bar.start_time == half_interval.duration


def test_holiday_resolves_to_no_session_interval() -> None:
    provider = ExchangeCalendarProvider(_CALENDAR)
    source = CalendarSessionIntervalSource(provider)

    # The holiday has no session interval, so daily consolidation can never
    # close a full day on it.
    assert source.interval_for_session_id(_HOLIDAY.isoformat()) is None
    assert source.interval_for_session_id(_FULL_SESSION_1.isoformat()) is not None


def test_fixed_window_would_misclose_half_day_unlike_calendar_source() -> None:
    """Regression guard: a fixed window ignores the half-day early close.

    A fixed ``RegularSessionWindow`` modelling the regular full-session close
    (17:00 ET == 23:00 UTC in winter) would close the Christmas Eve session at
    the full-session time, whereas the calendar source closes it early.
    """
    provider = ExchangeCalendarProvider(_CALENDAR)
    calendar_source = CalendarSessionIntervalSource(provider)

    fixed_window = RegularSessionWindow(
        exchange_timezone="America/New_York",
        open_time=datetime.strptime("18:00", "%H:%M").time(),
        close_time=datetime.strptime("17:00", "%H:%M").time(),
    )

    half_day_id = _HALF_DAY.isoformat()
    calendar_interval = calendar_source.interval_for_session_id(half_day_id)
    fixed_interval = fixed_window.interval_for_session_id(half_day_id)

    assert calendar_interval is not None
    # Calendar closes early; the fixed window does not — they must differ.
    assert calendar_interval.end != fixed_interval.end
    assert calendar_interval.end < fixed_interval.end


@pytest.mark.parametrize(
    ("session_date", "expected_full"),
    [
        (_FULL_SESSION_1, True),
        (_HALF_DAY, False),
        (_FULL_SESSION_2, True),
    ],
)
def test_full_versus_half_session_durations(session_date: date, expected_full: bool) -> None:
    provider = ExchangeCalendarProvider(_CALENDAR)
    interval = provider.session_interval_for(session_date)
    assert interval is not None
    is_full = interval.duration == timedelta(hours=24)
    assert is_full is expected_full
