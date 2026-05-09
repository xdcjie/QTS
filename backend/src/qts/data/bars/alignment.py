"""Clock and session bucket alignment helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, tzinfo

from qts.core.time import TimeInterval, to_exchange_time
from qts.data.bars.timeframe import AlignmentMode, Timeframe


def clock_bucket_for(
    timestamp: datetime,
    timeframe: Timeframe,
    exchange_timezone: str | tzinfo,
) -> TimeInterval:
    """Return the exchange-clock bucket containing ``timestamp``."""

    if timeframe.alignment is not AlignmentMode.CLOCK or timeframe.duration is None:
        raise ValueError("clock_bucket_for requires a clock-aligned timeframe")

    exchange_time = to_exchange_time(timestamp, exchange_timezone)
    seconds = _duration_seconds(timeframe.duration)
    midnight = exchange_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_seconds = (
        exchange_time.hour * 3600
        + exchange_time.minute * 60
        + exchange_time.second
        + exchange_time.microsecond / 1_000_000
    )
    bucket_seconds = int(elapsed_seconds // seconds) * seconds
    start = midnight + timedelta(seconds=bucket_seconds)
    end = start + timeframe.duration
    return TimeInterval(start=start, end=end)


def _duration_seconds(duration: timedelta) -> int:
    seconds = int(duration.total_seconds())
    if seconds <= 0:
        raise ValueError("timeframe duration must be positive")
    if 86_400 % seconds != 0:
        raise ValueError("clock timeframe must evenly divide a 24-hour day")
    return seconds


__all__ = ["clock_bucket_for"]
