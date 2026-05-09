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


__all__ = ["ComexGoldCalendarProvider"]
