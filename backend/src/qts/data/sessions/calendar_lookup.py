"""Calendar session lookup protocol shared by session-aware components."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from qts.registry.calendar_registry import MarketSession


class CalendarSessionLookup(Protocol):
    """Calendar session lookup required by session-aware components."""

    def session_for(self, calendar_id: str, session_date: date) -> MarketSession:
        """Return the internal market session for the date."""


__all__ = ["CalendarSessionLookup"]
