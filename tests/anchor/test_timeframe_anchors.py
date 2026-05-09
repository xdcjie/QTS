from __future__ import annotations

from datetime import timedelta


def test_daily_timeframe_is_session_aligned_not_twenty_four_hours() -> None:
    from qts.data.bars.timeframe import AlignmentMode, Timeframe

    daily = Timeframe.parse("1d")

    assert daily.alignment is AlignmentMode.SESSION
    assert daily.duration is None
    assert daily != Timeframe(
        value="24h", duration=timedelta(hours=24), alignment=AlignmentMode.CLOCK
    )
