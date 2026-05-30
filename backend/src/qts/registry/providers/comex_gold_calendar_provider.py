"""COMEX Gold product-specific calendar override."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from qts.core.time import TimeInterval
from qts.registry.calendar_registry import MarketSession


class ComexGoldCalendarProvider:
    """Regular COMEX Gold session provider for anchor-verified semantics."""

    calendar_id = "COMEX.GC"
    exchange_timezone = ZoneInfo("America/New_York")

    def session_for(self, session_date: date) -> MarketSession:
        """Perform session_for."""
        open_date = session_date - timedelta(days=1)
        open_time = datetime.combine(
            open_date,
            time(hour=18),
            tzinfo=self.exchange_timezone,
        )
        close_time = datetime.combine(
            session_date,
            time(hour=17),
            tzinfo=self.exchange_timezone,
        )
        return MarketSession(
            calendar_id=self.calendar_id,
            session_id=session_date.isoformat(),
            interval=TimeInterval(
                start=open_time.astimezone(ZoneInfo("UTC")),
                end=close_time.astimezone(ZoneInfo("UTC")),
            ),
        )

    def session_interval_for(self, session_date: date) -> TimeInterval:
        """Return the half-open DST-aware session interval for a close date.

        This provider models only the regular COMEX Gold session (no holiday
        or half-day calendar), so every date resolves to a session. The
        interval is DST-aware via ``America/New_York``: the exchange-local
        ``[18:00, 17:00)`` window is constant, but the UTC interval shortens
        on spring-forward and lengthens on fall-back.
        """
        return self.session_for(session_date).interval


__all__ = ["ComexGoldCalendarProvider"]
