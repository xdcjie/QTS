from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def test_five_minute_clock_buckets_are_half_open_across_hour_boundary() -> None:
    from qts.data.bars.alignment import clock_bucket_for
    from qts.data.bars.timeframe import Timeframe

    exchange_tz = ZoneInfo("America/New_York")
    bucket = clock_bucket_for(
        datetime(2026, 1, 2, 9, 59, 59, tzinfo=exchange_tz),
        Timeframe.parse("5m"),
        exchange_tz,
    )

    assert bucket.start == datetime(2026, 1, 2, 9, 55, tzinfo=exchange_tz)
    assert bucket.end == datetime(2026, 1, 2, 10, 0, tzinfo=exchange_tz)
    assert bucket.contains(datetime(2026, 1, 2, 9, 59, 59, tzinfo=exchange_tz))
    assert not bucket.contains(datetime(2026, 1, 2, 10, 0, tzinfo=exchange_tz))
