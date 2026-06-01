"""exchange-calendars backed provider hidden behind internal calendar interfaces."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import exchange_calendars as xc  # type: ignore[import-untyped]
from exchange_calendars.errors import NotSessionError  # type: ignore[import-untyped]

from qts.core.time import TimeInterval
from qts.registry.calendar_registry import MarketSession


class ExchangeCalendarProvider:
    """Calendar provider backed by ``exchange-calendars``."""

    def __init__(self, calendar_id: str) -> None:
        """Load the named exchange calendar, rejecting an empty id."""
        if not calendar_id.strip():
            raise ValueError("calendar_id must not be empty")
        self._calendar_id = calendar_id
        self._calendar: Any = xc.get_calendar(calendar_id)

    def session_for(self, session_date: date) -> MarketSession:
        """Return the market session (open/close interval) for the given date."""
        session_label = session_date.isoformat()
        open_time = self._to_datetime(self._calendar.session_open(session_label))
        close_time = self._to_datetime(self._calendar.session_close(session_label))
        return MarketSession(
            calendar_id=self._calendar_id,
            session_id=session_label,
            interval=TimeInterval(start=open_time, end=close_time),
        )

    def session_interval_for(self, session_date: date) -> TimeInterval | None:
        """Return the half-open session interval, or ``None`` if not a session.

        Holidays are not sessions and resolve to ``None``. Half-days resolve to
        the early-close interval. Keeping the library's ``NotSessionError``
        contained here preserves the calendar-library wrapping boundary.
        """
        try:
            session = self.session_for(session_date)
        except NotSessionError:
            return None
        return session.interval

    def session_offset(self, session_date: date, offset: int) -> date:
        """Return the exchange session date at ``offset`` from ``session_date``."""
        session = self._calendar.date_to_session(session_date.isoformat(), direction="previous")
        for _ in range(abs(offset)):
            if offset < 0:
                session = self._calendar.previous_session(session)
            else:
                session = self._calendar.next_session(session)
        return self._to_datetime(session).date()

    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        """Convert a calendar-library timestamp into a stdlib datetime."""
        try:
            converted = value.to_pydatetime()
        except AttributeError:
            converted = None
        if converted is not None and isinstance(converted, datetime):
            return converted
        if isinstance(value, datetime):
            return value
        raise TypeError(f"expected datetime-like calendar value, got {type(value).__name__}")


__all__ = ["ExchangeCalendarProvider"]
