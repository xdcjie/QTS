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
        """Validate that calendar_id and session_id are non-empty."""
        if not self.calendar_id.strip():
            raise ValueError("calendar_id must not be empty")
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")

    @property
    def open_time(self) -> datetime:
        """Return the session's open timestamp (interval start)."""
        return self.interval.start

    @property
    def close_time(self) -> datetime:
        """Return the session's close timestamp (interval end)."""
        return self.interval.end


class CalendarProvider(Protocol):
    """Provider interface for internal calendar session lookup."""

    def session_for(self, session_date: date) -> MarketSession:
        """Return the exchange session for a date."""


class CalendarRegistry:
    """Lookup table for calendar providers."""

    def __init__(self) -> None:
        """Initialize an empty calendar-id to provider lookup table."""
        self._providers: dict[str, CalendarProvider] = {}

    def register(self, calendar_id: str, provider: CalendarProvider) -> None:
        """Register a calendar provider under the given calendar id."""
        if not calendar_id.strip():
            raise ValueError("calendar_id must not be empty")
        self._providers[calendar_id] = provider

    def session_for(self, calendar_id: str, session_date: date) -> MarketSession:
        """Return the session for a date from the named calendar, raising if unregistered."""
        try:
            provider = self._providers[calendar_id]
        except KeyError as exc:
            raise KeyError(f"calendar not registered: {calendar_id}") from exc
        return provider.session_for(session_date)


__all__ = ["CalendarProvider", "CalendarRegistry", "MarketSession"]
