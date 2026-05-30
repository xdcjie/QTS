"""Clock and session bucket alignment helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo

from qts.core.time import TimeInterval, to_exchange_time
from qts.data.bars.timeframe import AlignmentMode, Timeframe


def clock_bucket_for(
    timestamp: datetime,
    timeframe: Timeframe,
    exchange_timezone: str | tzinfo,
) -> TimeInterval:
    """Return the exchange-clock bucket containing ``timestamp``.

    Buckets align to wall-clock multiples of the timeframe duration in the
    exchange timezone, but they tile the *real* timeline. Across a
    daylight-saving fall-back the repeated wall-clock hour yields two distinct
    buckets (disambiguated by ``fold``); across a spring-forward the skipped
    hour yields none. The bucket end therefore advances by the real elapsed
    duration, never by naive wall-clock arithmetic -- the latter resets
    ``fold`` and would collapse the two fall-back occurrences onto a single
    instant, silently dropping the repeated hour during consolidation.
    """

    if timeframe.alignment is not AlignmentMode.CLOCK or timeframe.duration is None:
        raise ValueError("clock_bucket_for requires a clock-aligned timeframe")

    timezone: tzinfo = (
        ZoneInfo(exchange_timezone) if isinstance(exchange_timezone, str) else exchange_timezone
    )
    exchange_time = to_exchange_time(timestamp, timezone)
    seconds = _duration_seconds(timeframe.duration)
    midnight = exchange_time.replace(hour=0, minute=0, second=0, microsecond=0, fold=0)
    elapsed_seconds = (
        exchange_time.hour * 3600
        + exchange_time.minute * 60
        + exchange_time.second
        + exchange_time.microsecond / 1_000_000
    )
    bucket_seconds = int(elapsed_seconds // seconds) * seconds
    # Pin the wall-clock bucket start to the same DST occurrence (``fold``) as
    # the source instant, then carry the bucket as UTC instants. Same-zone
    # datetime comparison ignores ``fold`` (it compares wall-clock fields), so
    # an exchange-local representation would make the two fall-back occurrences
    # of a repeated hour compare *equal*; UTC keeps bucket identity and
    # ordering instant-based.
    start_local = (midnight + timedelta(seconds=bucket_seconds)).replace(fold=exchange_time.fold)
    start = start_local.astimezone(UTC)
    # UTC has no DST, so adding the duration advances by real elapsed time and
    # contiguous buckets tile the real timeline across transitions.
    end = start + timeframe.duration
    return TimeInterval(start=start, end=end)


def _duration_seconds(duration: timedelta) -> int:
    """Perform _duration_seconds."""
    seconds = int(duration.total_seconds())
    if seconds <= 0:
        raise ValueError("timeframe duration must be positive")
    if 86_400 % seconds != 0:
        raise ValueError("clock timeframe must evenly divide a 24-hour day")
    return seconds


__all__ = ["clock_bucket_for"]
