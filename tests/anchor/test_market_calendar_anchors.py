from __future__ import annotations

from datetime import date, timedelta
from zoneinfo import ZoneInfo


def test_comex_gold_regular_session_has_1380_one_minute_bars() -> None:
    from qts.registry.providers.comex_gold_calendar_provider import ComexGoldCalendarProvider

    provider = ComexGoldCalendarProvider()
    session = provider.session_for(date(2026, 1, 6))
    exchange_tz = ZoneInfo("America/New_York")

    assert session.open_time.astimezone(exchange_tz).isoformat() == "2026-01-05T18:00:00-05:00"
    assert session.close_time.astimezone(exchange_tz).isoformat() == "2026-01-06T17:00:00-05:00"
    assert session.interval.duration == timedelta(hours=23)
    assert int(session.interval.duration / timedelta(minutes=1)) == 1380


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
