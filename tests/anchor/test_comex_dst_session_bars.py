"""Anchor: COMEX Gold one-minute bar counts honour DST session transitions.

Domain fact (``docs/domain/market_calendar_and_sessions.md``): market
sessions are domain facts; timezones are representations. The COMEX Gold
regular session is the exchange-local ``[18:00, 17:00)`` window in
``America/New_York``. That clock window is constant year-round, but the
resulting UTC interval -- and therefore the number of one-minute
``[start, end)`` slots that tile it -- depends on daylight-saving:

- normal day: 23h -> 1380 one-minute bars
- spring-forward day (clocks skip 02:00->03:00 ET): 22h -> 1320 bars
- fall-back day (clocks repeat 01:00-02:00 ET): 24h -> 1440 bars

1380 is the NORMAL non-transition count, not a universal invariant.
Asserting 1380 (or 1440/1379) unconditionally is wrong on DST days.

Owner: ``ComexGoldCalendarProvider.session_for`` derives the DST-aware
interval; ``BarTimeGridSynthesizer`` tiles it into contiguous
one-minute bars with no phantom or gap.

Forbidden shortcut: hardcoding 1380 for every session; computing the
count from a fixed 23h window instead of the DST-aware interval.
"""

from __future__ import annotations

import itertools
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.data.bars.time_grid_synthesizer import BarTimeGridSynthesizer
from qts.domain.market_data import Bar
from qts.registry.providers.comex_gold_calendar_provider import ComexGoldCalendarProvider

_INSTRUMENT = InstrumentId("FUTURE.US.COMEX.GC")
_ONE_MINUTE = timedelta(minutes=1)


def _one_minute_bar(*, start: datetime, session_id: str) -> Bar:
    """Build one real one-minute bar used as a synthesis anchor."""
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
    )


def _expected_minute_count(session_date: date) -> int:
    """One-minute slot count tiling the DST-aware session interval."""
    interval = ComexGoldCalendarProvider().session_for(session_date).interval
    return int(interval.duration / _ONE_MINUTE)


@pytest.mark.parametrize(
    ("session_date", "expected_bars"),
    [
        (date(2026, 1, 6), 1380),  # normal day: 23h
        (date(2026, 3, 8), 1320),  # spring-forward: 22h (02:00->03:00 ET skipped)
        (date(2026, 11, 1), 1440),  # fall-back: 24h (01:00-02:00 ET repeated)
    ],
)
def test_comex_gold_one_minute_bar_count_tracks_dst_transition(
    session_date: date,
    expected_bars: int,
) -> None:
    assert _expected_minute_count(session_date) == expected_bars


@pytest.mark.parametrize(
    ("session_date", "expected_bars"),
    [
        (date(2026, 1, 6), 1380),
        (date(2026, 3, 8), 1320),
        (date(2026, 11, 1), 1440),
    ],
)
def test_synthesizer_tiles_dst_session_cleanly_with_no_phantom_or_gap(
    session_date: date,
    expected_bars: int,
) -> None:
    """The synthesizer fills a session from open to close with exactly
    ``expected_bars`` contiguous ``[start, end)`` one-minute bars."""
    interval = ComexGoldCalendarProvider().session_for(session_date).interval
    session_id = session_date.isoformat()

    # Two real anchors: the opening slot and the closing slot. The synthesizer
    # fills every minute in between, tiling the whole session.
    first = _one_minute_bar(start=interval.start, session_id=session_id)
    last = _one_minute_bar(start=interval.end - _ONE_MINUTE, session_id=session_id)

    output = list(BarTimeGridSynthesizer(timeframe="1m").synthesize(iter([first, last])))

    # Exactly one bar per minute slot in the session.
    assert len(output) == expected_bars

    # Bars tile the session with no phantom bars outside [open, close) and no gap.
    assert output[0].start_time == interval.start
    assert output[-1].end_time == interval.end
    for bar in output:
        assert bar.end_time - bar.start_time == _ONE_MINUTE
        assert interval.start <= bar.start_time
        assert bar.end_time <= interval.end
    for left, right in itertools.pairwise(output):
        assert left.end_time == right.start_time
