from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def test_clock_bucket_alignment_uses_exchange_timezone() -> None:
    from qts.data.bars.alignment import clock_bucket_for
    from qts.data.bars.timeframe import Timeframe

    exchange_tz = ZoneInfo("America/New_York")
    bucket = clock_bucket_for(
        datetime(2026, 1, 2, 9, 32, tzinfo=exchange_tz),
        Timeframe.parse("5m"),
        exchange_tz,
    )

    assert bucket.start == datetime(2026, 1, 2, 9, 30, tzinfo=exchange_tz)
    assert bucket.end == datetime(2026, 1, 2, 9, 35, tzinfo=exchange_tz)


def test_clock_bucket_end_boundary_belongs_to_next_bucket() -> None:
    from qts.data.bars.alignment import clock_bucket_for
    from qts.data.bars.timeframe import Timeframe

    exchange_tz = ZoneInfo("America/New_York")
    bucket = clock_bucket_for(
        datetime(2026, 1, 2, 9, 35, tzinfo=exchange_tz),
        Timeframe.parse("5m"),
        exchange_tz,
    )

    assert bucket.start == datetime(2026, 1, 2, 9, 35, tzinfo=exchange_tz)
    assert bucket.end == datetime(2026, 1, 2, 9, 40, tzinfo=exchange_tz)
