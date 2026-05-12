"""Regular exchange session window definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from qts.core.time import to_exchange_time


@dataclass(frozen=True, slots=True)
class RegularSessionWindow:
    """A recurring half-open exchange session window.

    The session id is the exchange-local close date. For overnight sessions this
    means a bar at or after the open belongs to the next local date's session.
    """

    exchange_timezone: str
    open_time: time
    close_time: time

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.exchange_timezone.strip():
            raise ValueError("exchange_timezone must not be empty")
        if self.open_time == self.close_time:
            raise ValueError("open_time and close_time must differ")

    def session_id_for_timestamp(self, timestamp: datetime) -> str | None:
        """Return the exchange-local close-date session id containing timestamp."""

        session_date = self.session_date_for_timestamp(timestamp)
        return session_date.isoformat() if session_date is not None else None

    def session_date_for_timestamp(self, timestamp: datetime) -> date | None:
        """Return the exchange-local close date for timestamp, or None if outside."""

        local_timestamp = to_exchange_time(timestamp, self.exchange_timezone)
        local_time = local_timestamp.time()
        if self.open_time < self.close_time:
            if self.open_time <= local_time < self.close_time:
                return local_timestamp.date()
            return None
        if local_time >= self.open_time:
            return local_timestamp.date() + timedelta(days=1)
        if local_time < self.close_time:
            return local_timestamp.date()
        return None

    def to_payload(self) -> dict[str, str]:
        """Return a stable JSON-serializable description of the session rule."""

        return {
            "id_policy": "exchange_local_close_date",
            "timezone": self.exchange_timezone,
            "interval": f"[{self.open_time:%H:%M},{self.close_time:%H:%M})",
        }


__all__ = ["RegularSessionWindow"]
