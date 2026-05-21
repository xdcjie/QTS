from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


def _regular_session_duration(root: str) -> timedelta:
    from qts.data.historical.chains import HistoricalChain

    chain = HistoricalChain.load(Path("historical/chains") / f"{root}.json")
    window = chain.session_window()
    assert window is not None
    exchange_tz = ZoneInfo(window.exchange_timezone)
    close_date = date(2026, 1, 6)
    if window.open_time < window.close_time:
        open_date = close_date
    else:
        open_date = close_date - timedelta(days=1)
    session_open = datetime.combine(open_date, window.open_time, tzinfo=exchange_tz)
    session_close = datetime.combine(close_date, window.close_time, tzinfo=exchange_tz)
    return session_close - session_open


def test_comex_gold_regular_session_has_exchange_local_23_hour_window() -> None:
    from qts.registry.providers.comex_gold_calendar_provider import ComexGoldCalendarProvider

    provider = ComexGoldCalendarProvider()
    session = provider.session_for(date(2026, 1, 6))
    exchange_tz = ZoneInfo("America/New_York")

    assert session.open_time.astimezone(exchange_tz).isoformat() == "2026-01-05T18:00:00-05:00"
    assert session.close_time.astimezone(exchange_tz).isoformat() == "2026-01-06T17:00:00-05:00"
    assert session.interval.duration == timedelta(hours=23)


@pytest.mark.parametrize(
    ("root", "timeframe", "expected_bars"),
    [
        ("GC", "1m", 1380),
        ("GC", "5m", 276),
        ("GC", "15m", 92),
        ("SI", "1m", 1380),
        ("SI", "5m", 276),
        ("SI", "15m", 92),
    ],
)
def test_comex_metals_regular_session_bar_count_by_clock_timeframe(
    root: str,
    timeframe: str,
    expected_bars: int,
) -> None:
    from qts.data.bars.timeframe import AlignmentMode, Timeframe

    parsed = Timeframe.parse(timeframe)

    assert parsed.alignment is AlignmentMode.CLOCK
    assert parsed.duration is not None
    assert _regular_session_duration(root) == parsed.duration * expected_bars


def test_comex_gold_session_count_is_timezone_representation_independent() -> None:
    from qts.registry.providers.comex_gold_calendar_provider import ComexGoldCalendarProvider

    provider = ComexGoldCalendarProvider()
    session = provider.session_for(date(2026, 1, 6))

    utc_minutes = int((session.close_time - session.open_time) / timedelta(minutes=1))
    cst_minutes = int(
        (
            session.close_time.astimezone(ZoneInfo("Asia/Shanghai"))
            - session.open_time.astimezone(ZoneInfo("Asia/Shanghai"))
        )
        / timedelta(minutes=1)
    )

    assert utc_minutes == 1380
    assert cst_minutes == 1380
