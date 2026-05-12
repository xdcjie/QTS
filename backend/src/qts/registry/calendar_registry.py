"""Internal market calendar registry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from qts.core.time import TimeInterval


@dataclass(frozen=True, slots=True)
class MarketSession:
    """Internal half-open exchange session."""

    calendar_id: str
    session_id: str
    interval: TimeInterval

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.calendar_id.strip():
            raise ValueError("calendar_id must not be empty")
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")

    @property
    def open_time(self) -> datetime:
        """Perform open_time."""
        return self.interval.start

    @property
    def close_time(self) -> datetime:
        """Perform close_time."""
        return self.interval.end


class CalendarProvider(Protocol):
    """Provider interface for internal calendar session lookup."""

    def session_for(self, session_date: date) -> MarketSession:
        """Return the exchange session for a date."""


class CalendarRegistry:
    """Lookup table for calendar providers."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._providers: dict[str, CalendarProvider] = {}

    def register(self, calendar_id: str, provider: CalendarProvider) -> None:
        """Perform register."""
        if not calendar_id.strip():
            raise ValueError("calendar_id must not be empty")
        self._providers[calendar_id] = provider

    def session_for(self, calendar_id: str, session_date: date) -> MarketSession:
        """Perform session_for."""
        try:
            provider = self._providers[calendar_id]
        except KeyError as exc:
            raise KeyError(f"calendar not registered: {calendar_id}") from exc
        return provider.session_for(session_date)


__all__ = ["CalendarProvider", "CalendarRegistry", "MarketSession"]
