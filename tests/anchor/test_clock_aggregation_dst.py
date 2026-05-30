"""Anchor: clock-aligned intraday aggregation tiles the real timeline across DST.

Domain fact (``docs/domain/market_calendar_and_sessions.md``,
``docs/domain/bar_timeframe_model.md``): clock-aligned ``<1d`` bars tile the
*real* timeline with ``[start, end)`` slots. Across a daylight-saving fall-back
the repeated wall-clock hour is two physically distinct intervals (they must not
collapse into one); across a spring-forward the skipped hour produces no bars.
The bucket end advances by the real elapsed duration, never by naive wall-clock
arithmetic.

Owner: ``clock_bucket_for`` (``qts.data.bars.alignment``) -- the point->bucket
function shared by ``BarAggregator`` and ``NMinuteConsolidator``. It must agree
with the real-time grid that ``BarTimeGridSynthesizer`` tiles.

Forbidden shortcut: bucketing by wall-clock fields and rebuilding the start with
``midnight + timedelta`` (which resets ``fold`` and collapses the two fall-back
occurrences onto a single instant, silently dropping the repeated hour during
consolidation), or representing buckets as fold-blind exchange-local datetimes
(same-zone datetime comparison ignores ``fold``, so the two occurrences would
compare equal).

This anchor drives the PRODUCTION consolidation path (``NMinuteConsolidator``),
closing the gap left by ``test_comex_dst_session_bars.py``, which only exercises
the synthesizer's own real-time grid and never the point->bucket assignment.
"""

from __future__ import annotations

import itertools
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from qts.core.ids import InstrumentId
from qts.core.time import to_exchange_time
from qts.data.bars.alignment import clock_bucket_for
from qts.data.bars.consolidator import NMinuteConsolidator
from qts.data.bars.time_grid_synthesizer import BarTimeGridSynthesizer
from qts.data.bars.timeframe import Timeframe
from qts.domain.market_data import Bar
from qts.registry.providers.comex_gold_calendar_provider import ComexGoldCalendarProvider

_EXCHANGE_TZ = ZoneInfo("America/New_York")
_INSTRUMENT = InstrumentId("FUTURE.US.COMEX.GC")
_ONE_MINUTE = timedelta(minutes=1)
_FIVE_MINUTES = timedelta(minutes=5)


def _one_minute_bar(*, start: datetime, session_id: str) -> Bar:
    """Build one complete one-minute source bar."""
    price = Decimal("2000.0")
    return Bar(
        instrument_id=_INSTRUMENT,
        start_time=start,
        end_time=start + _ONE_MINUTE,
        timeframe="1m",
        session_id=session_id,
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal("1"),
        is_complete=True,
        is_partial=False,
    )


def _session_one_minute_grid(session_date: date) -> list[Bar]:
    """Synthesize the full, DST-aware one-minute grid for a COMEX Gold session."""
    interval = ComexGoldCalendarProvider().session_for(session_date).interval
    session_id = session_date.isoformat()
    first = _one_minute_bar(start=interval.start, session_id=session_id)
    last = _one_minute_bar(start=interval.end - _ONE_MINUTE, session_id=session_id)
    return list(BarTimeGridSynthesizer(timeframe="1m").synthesize(iter([first, last])))


def _consolidate_to_five_minutes(grid: list[Bar]) -> list[Bar]:
    """Run the production 1m->5m consolidator over a one-minute grid."""
    consolidator = NMinuteConsolidator(
        source_timeframe=Timeframe.parse("1m"),
        target_timeframe=Timeframe.parse("5m"),
        exchange_timezone=_EXCHANGE_TZ,
    )
    completed: list[Bar] = []
    for bar in grid:
        completed.extend(consolidator.update(bar))
    return completed


def test_clock_bucket_for_does_not_collapse_repeated_fall_back_hour() -> None:
    """The two real occurrences of 01:30 ET on a fall-back day get distinct buckets."""
    timeframe = Timeframe.parse("5m")
    # 2026-11-01: clocks fall back at 02:00 EDT -> 01:00 EST, so 01:30 ET happens
    # twice: 05:30Z (EDT, fold=0) and 06:30Z (EST, fold=1), one real hour apart.
    first = clock_bucket_for(datetime(2026, 11, 1, 5, 30, tzinfo=UTC), timeframe, _EXCHANGE_TZ)
    second = clock_bucket_for(datetime(2026, 11, 1, 6, 30, tzinfo=UTC), timeframe, _EXCHANGE_TZ)

    assert first != second
    assert first.start == datetime(2026, 11, 1, 5, 30, tzinfo=UTC)
    assert second.start == datetime(2026, 11, 1, 6, 30, tzinfo=UTC)
    # Each bucket spans exactly five real minutes (not a wall-clock artifact).
    assert first.end - first.start == _FIVE_MINUTES
    assert second.end - second.start == _FIVE_MINUTES
    # The two occurrences are exactly one real hour apart.
    assert second.start - first.start == timedelta(hours=1)


@pytest.mark.parametrize(
    ("session_date", "expected_five_minute_bars", "buckets_in_0100_hour", "buckets_in_0200_hour"),
    [
        # normal day: 23h session -> 276 five-minute bars; each ET hour once.
        (date(2026, 1, 6), 276, 12, 12),
        # spring-forward: 22h -> 264; the 02:00 ET hour is skipped (0 buckets).
        (date(2026, 3, 8), 264, 12, 0),
        # fall-back: 24h -> 288; the 01:00 ET hour repeats (24 buckets = 12 x 2).
        (date(2026, 11, 1), 288, 24, 12),
    ],
)
def test_five_minute_consolidation_tiles_real_timeline_across_dst(
    session_date: date,
    expected_five_minute_bars: int,
    buckets_in_0100_hour: int,
    buckets_in_0200_hour: int,
) -> None:
    """The production consolidator emits one contiguous bucket per real 5m slot.

    No collapse on fall-back (every emitted start is a distinct instant, the
    repeated hour appears twice) and no phantom bucket in the spring-forward gap.
    """
    grid = _session_one_minute_grid(session_date)
    completed = _consolidate_to_five_minutes(grid)

    # Exactly one complete 5m bar per real slot; the session length divides by 5.
    assert len(completed) == expected_five_minute_bars

    # No collision and no data loss: every emitted bucket start is a distinct
    # real instant (a fold-blind bug would yield duplicates / fewer uniques).
    start_instants = [bar.start_time.astimezone(UTC) for bar in completed]
    assert len(set(start_instants)) == expected_five_minute_bars

    # Each emitted bar covers exactly five real minutes...
    for bar in completed:
        assert bar.end_time - bar.start_time == _FIVE_MINUTES
    # ...and the buckets tile the session contiguously with no gap or overlap.
    for earlier, later in itertools.pairwise(completed):
        assert earlier.end_time == later.start_time

    # DST occurrence accounting in exchange-local terms: the repeated fall-back
    # hour yields twice the buckets; the skipped spring-forward hour yields none.
    in_0100 = sum(
        1 for bar in completed if to_exchange_time(bar.start_time, _EXCHANGE_TZ).hour == 1
    )
    in_0200 = sum(
        1 for bar in completed if to_exchange_time(bar.start_time, _EXCHANGE_TZ).hour == 2
    )
    assert in_0100 == buckets_in_0100_hour
    assert in_0200 == buckets_in_0200_hour
