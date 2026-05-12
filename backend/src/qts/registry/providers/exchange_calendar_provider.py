"""exchange-calendars backed provider hidden behind internal calendar interfaces."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import exchange_calendars as xc  # type: ignore[import-untyped]

from qts.core.time import TimeInterval
from qts.registry.calendar_registry import MarketSession


class ExchangeCalendarProvider:
    """Calendar provider backed by ``exchange-calendars``."""

    def __init__(self, calendar_id: str) -> None:
        """Perform __init__."""
        if not calendar_id.strip():
            raise ValueError("calendar_id must not be empty")
        self._calendar_id = calendar_id
        self._calendar: Any = xc.get_calendar(calendar_id)

    def session_for(self, session_date: date) -> MarketSession:
        """Perform session_for."""
        session_label = session_date.isoformat()
        open_time = self._to_datetime(self._calendar.session_open(session_label))
        close_time = self._to_datetime(self._calendar.session_close(session_label))
        return MarketSession(
            calendar_id=self._calendar_id,
            session_id=session_label,
            interval=TimeInterval(start=open_time, end=close_time),
        )

    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        """Perform _to_datetime."""
        if hasattr(value, "to_pydatetime"):
            converted = value.to_pydatetime()
            if isinstance(converted, datetime):
                return converted
        if isinstance(value, datetime):
            return value
        raise TypeError(f"expected datetime-like calendar value, got {type(value).__name__}")


__all__ = ["ExchangeCalendarProvider"]
