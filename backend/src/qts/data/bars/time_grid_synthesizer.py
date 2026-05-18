"""Fill clock-aligned `<1d` bars to a complete time grid within each session.

Convention used by most live realtime market-data feeds: clock-aligned
intraday bars emit one bar per wall-clock slot, even when the
underlying tape was silent. Missing slots get
``OHLC = previous close`` and ``volume = 0``, flagged via
``Bar.is_synthetic = True`` so downstream code can distinguish them
from real prints.

This wrapper turns a sparse, trade-only bar stream (the historical
format ``ReplayMarketDataSource`` emits today) into a
time-grid-complete stream. The synthesizer is session-aware: a gap
that straddles two ``session_id`` values is not bridged, because the
gap is a natural break (e.g. a daily session close), not a data
quality issue.

Per-instrument state lets multi-instrument feeds work correctly: a
gap in one symbol's tape is filled with that symbol's last close,
independent of whether other symbols had bars during the same minutes.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.data.bars.timeframe import AlignmentMode, Timeframe
from qts.domain.market_data import Bar


@dataclass(slots=True)
class _InstrumentState:
    """Per-instrument cursor used to detect and fill intra-session gaps."""

    last_bar: Bar | None = None


class BarTimeGridSynthesizer:
    """Wrap a sparse clock-aligned bar stream into a time-grid-complete stream.

    Only ``CLOCK`` alignment is supported; ``1d`` (session-aligned)
    bars carry their own time grid via session boundaries and are not
    candidates for minute-level synthesis.
    """

    def __init__(self, *, timeframe: str) -> None:
        parsed = Timeframe.parse(timeframe)
        if parsed.alignment is not AlignmentMode.CLOCK or parsed.duration is None:
            raise ValueError(
                f"BarTimeGridSynthesizer only supports clock-aligned timeframes; got {timeframe!r}"
            )
        self._timeframe_value = parsed.value
        self._slot_duration: timedelta = parsed.duration

    def synthesize(self, bars: Iterable[Bar]) -> Iterator[Bar]:
        """Yield bars with intra-session gaps filled by synthetic bars.

        Synthetic bars: ``open = high = low = close = previous close``,
        ``volume = 0``, ``is_synthetic = True``. Same ``instrument_id``,
        ``timeframe``, ``session_id`` as the trailing real bar.
        """
        cursors: dict[InstrumentId, _InstrumentState] = {}
        for bar in bars:
            cursor = cursors.setdefault(bar.instrument_id, _InstrumentState())
            previous = cursor.last_bar
            if previous is not None and self._should_fill_between(previous, bar):
                yield from self._fill_gap(previous=previous, next_bar=bar)
            yield bar
            cursor.last_bar = bar

    def _should_fill_between(self, previous: Bar, next_bar: Bar) -> bool:
        """Decide whether to synthesize bars in the gap between two real bars."""
        if previous.session_id != next_bar.session_id:
            return False
        if next_bar.timeframe != self._timeframe_value:
            return False
        return next_bar.start_time > previous.end_time

    def _fill_gap(self, *, previous: Bar, next_bar: Bar) -> Iterator[Bar]:
        """Emit one synthetic bar per missing slot in the half-open gap."""
        cursor_start = previous.end_time
        while cursor_start < next_bar.start_time:
            slot_end = cursor_start + self._slot_duration
            if slot_end > next_bar.start_time:
                # Last slot would overlap the next observed bar — stop short.
                break
            yield self._synthetic_bar(template=previous, start=cursor_start, end=slot_end)
            cursor_start = slot_end

    @staticmethod
    def _synthetic_bar(*, template: Bar, start: datetime, end: datetime) -> Bar:
        """Build one synthetic bar carrying ``template``'s close as flat OHLC."""
        flat = template.close
        return replace(
            template,
            start_time=start,
            end_time=end,
            open=flat,
            high=flat,
            low=flat,
            close=flat,
            volume=Decimal("0"),
            vwap=None,
            open_interest=None,
            trade_count=None,
            is_synthetic=True,
            is_complete=True,
            is_partial=False,
        )


__all__ = ["BarTimeGridSynthesizer"]
