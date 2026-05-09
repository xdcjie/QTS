from __future__ import annotations

from datetime import date

import pytest


def test_exchange_calendar_provider_returns_internal_session_objects() -> None:
    from qts.registry.calendar_registry import CalendarRegistry, MarketSession
    from qts.registry.providers.exchange_calendar_provider import ExchangeCalendarProvider

    registry = CalendarRegistry()
    registry.register("XNYS", ExchangeCalendarProvider("XNYS"))

    session = registry.session_for("XNYS", date(2026, 1, 2))

    assert isinstance(session, MarketSession)
    assert session.calendar_id == "XNYS"
    assert session.session_id == "2026-01-02"
    assert session.open_time.isoformat() == "2026-01-02T14:30:00+00:00"
    assert session.close_time.isoformat() == "2026-01-02T21:00:00+00:00"
    assert session.open_time < session.close_time
    assert not session.__class__.__module__.startswith("exchange_calendars")


def test_calendar_registry_reports_missing_calendars_explicitly() -> None:
    from qts.registry.calendar_registry import CalendarRegistry

    registry = CalendarRegistry()

    with pytest.raises(KeyError, match="calendar not registered"):
        registry.session_for("MISSING", date(2026, 1, 2))
