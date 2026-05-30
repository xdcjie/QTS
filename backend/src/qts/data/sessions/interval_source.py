"""Session-interval sources used by calendar-aware daily consolidation.

Daily (``1d``) consolidation closes a day at its session boundary. A fixed
``RegularSessionWindow`` assumes every session has identical open/close
clock times, which is wrong for holidays (no session), half-days (early
close), and daylight-saving transitions (the exchange-local open/close
clock times are constant, but the resulting UTC interval -- and therefore
the number of one-minute slots -- is 1320 on spring-forward and 1440 on
fall-back instead of the normal 1380).

``SessionIntervalSource`` is the narrow dependency the consolidator needs:
given a close-date ``session_id``, return the half-open session interval, or
``None`` when that date is not a trading session. ``RegularSessionWindow``
satisfies this structurally for fixed-window streams; ``CalendarSessionIntervalSource``
derives the interval from a calendar provider so daily consolidation honours
holidays, half-days, and DST as domain facts rather than fixed-clock guesses.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from qts.core.time import TimeInterval


class SessionIntervalSource(Protocol):
    """Resolve a close-date session id to its half-open session interval."""

    def interval_for_session_id(self, session_id: str | date) -> TimeInterval | None:
        """Return the session interval, or ``None`` if the date is not a session."""


class _IntervalCalendarProvider(Protocol):
    """Calendar provider that resolves a session date to its interval.

    The provider owns the calendar-library boundary and returns ``None`` for
    non-session dates (holidays) instead of raising, so this data-layer source
    stays free of provider-specific exception types.
    """

    def session_interval_for(self, session_date: date) -> TimeInterval | None:
        """Return the session interval, or ``None`` if not a trading session."""


class CalendarSessionIntervalSource:
    """Derive daily session intervals from a calendar provider.

    Backed by any provider exposing ``session_interval_for(date) -> TimeInterval | None``
    (e.g. ``ExchangeCalendarProvider`` for holiday/half-day awareness or
    ``ComexGoldCalendarProvider`` for DST-aware COMEX sessions). Replaces the
    fixed-window assumption for ``1d`` consolidation: holidays resolve to
    ``None`` (no full daily bar), half-days resolve to the early close, and
    DST days resolve to the correct shortened/lengthened interval.
    """

    def __init__(self, provider: _IntervalCalendarProvider) -> None:
        """Perform __init__."""
        self._provider = provider

    def interval_for_session_id(self, session_id: str | date) -> TimeInterval | None:
        """Return the calendar session interval for a close-date session id.

        Returns ``None`` when the date is not a trading session (holiday),
        so daily consolidation never treats a non-session day as a full day.
        """
        session_date = date.fromisoformat(session_id) if isinstance(session_id, str) else session_id
        return self._provider.session_interval_for(session_date)


__all__ = ["CalendarSessionIntervalSource", "SessionIntervalSource"]
