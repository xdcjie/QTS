"""Time interval helpers. Use half-open intervals `[start, end)`."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo


def require_aware_datetime(value: datetime, *, name: str) -> None:
    """Validate that a datetime has an effective timezone."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def to_exchange_time(value: datetime, exchange_timezone: str | tzinfo) -> datetime:
    """Convert a timestamp representation into an exchange timezone."""

    require_aware_datetime(value, name="value")
    timezone = (
        ZoneInfo(exchange_timezone) if isinstance(exchange_timezone, str) else exchange_timezone
    )
    return value.astimezone(timezone)


@dataclass(frozen=True, slots=True)
class TimeInterval:
    """A half-open time interval with `[start, end)` membership."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        require_aware_datetime(self.start, name="start")
        require_aware_datetime(self.end, name="end")
        if self.start >= self.end:
            raise ValueError("start must be before end")

    @property
    def duration(self) -> timedelta:
        """Perform duration."""
        return self.end - self.start

    def contains(self, value: datetime) -> bool:
        """Perform contains."""
        require_aware_datetime(value, name="value")
        return self.start <= value < self.end


__all__ = ["TimeInterval", "require_aware_datetime", "to_exchange_time"]
