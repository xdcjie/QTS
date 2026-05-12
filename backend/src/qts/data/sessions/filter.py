"""Filter market data bars to exchange sessions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Protocol

from qts.domain.market_data import Bar
from qts.registry.calendar_registry import MarketSession


class SessionLookup(Protocol):
    """Calendar session lookup required by session filters."""

    def session_for(self, calendar_id: str, session_date: date) -> MarketSession:
        """Return the internal market session for the date."""


def filter_session_bars(
    bars: Iterable[Bar],
    *,
    calendar_registry: SessionLookup,
    calendar_id: str,
    session_date: date,
) -> list[Bar]:
    """Return bars whose start and end fall inside the half-open session."""

    session = calendar_registry.session_for(calendar_id, session_date)
    return [bar for bar in bars if _bar_inside_session(bar, session)]


def _bar_inside_session(bar: Bar, session: MarketSession) -> bool:
    """Perform _bar_inside_session."""
    return (
        session.interval.contains(bar.start_time)
        and bar.end_time <= session.close_time
        and bar.end_time > session.open_time
    )


__all__ = ["filter_session_bars"]
