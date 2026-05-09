from __future__ import annotations

from datetime import timedelta

import pytest


def test_timeframe_parse_distinguishes_clock_and_session_alignment() -> None:
    from qts.data.bars.timeframe import AlignmentMode, Timeframe

    assert Timeframe.parse("5s").alignment is AlignmentMode.CLOCK
    assert Timeframe.parse("4h").duration == timedelta(hours=4)
    assert Timeframe.parse("1d").alignment is AlignmentMode.SESSION
    assert Timeframe.parse("1d").duration is None


def test_timeframe_parse_rejects_unsupported_values() -> None:
    from qts.data.bars.timeframe import Timeframe

    with pytest.raises(ValueError, match="unsupported timeframe"):
        Timeframe.parse("2m")
    with pytest.raises(ValueError, match="unsupported timeframe"):
        Timeframe.parse("24h")
