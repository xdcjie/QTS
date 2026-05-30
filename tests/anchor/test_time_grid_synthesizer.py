"""Anchor: clock-aligned <1d bars must be time-grid complete within a session.

Domain fact: ``docs/domain/bar_timeframe_model.md`` says ``<1d`` bars
are clock-aligned in exchange timezone with ``[start, end)`` semantics.
Industry practice (Lean, Zipline, IBKR realtime) emits a bar for every
wall-clock minute slot — missing minutes get OHLC=previous close,
volume=0, marked synthetic. Without this, indicator windows (``EMA(20)``
etc.) drift across wall-clock time, and 1m→5m aggregation produces
partial bars whenever a minute had no trade.

Owner: ``qts.data.bars.time_grid_synthesizer.BarTimeGridSynthesizer``.

Forbidden shortcut: filling across session boundaries; fabricating
leading or trailing bars when no previous close exists; mutating
volume of real (non-synthetic) bars.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.data.bars.time_grid_synthesizer import BarTimeGridSynthesizer
from qts.domain.market_data import Bar

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")
_SESSION = "2026-01-02"


def _bar(
    *,
    minute: int,
    close: str,
    session: str = _SESSION,
    is_synthetic: bool = False,
    volume: str = "100",
) -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=minute)
    price = Decimal(close)
    return Bar(
        instrument_id=_INSTRUMENT,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id=session,
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal(volume),
        is_complete=True,
        is_synthetic=is_synthetic,
    )


def test_synthesizer_fills_missing_minutes_with_previous_close() -> None:
    """Gap fill: minute :02 and :03 are missing, must be synthesized."""
    sparse = [
        _bar(minute=0, close="100"),
        _bar(minute=1, close="101"),
        _bar(minute=4, close="104"),
    ]
    synthesizer = BarTimeGridSynthesizer(timeframe="1m")
    output = list(synthesizer.synthesize(iter(sparse)))

    assert [bar.start_time.minute for bar in output] == [30, 31, 32, 33, 34]
    assert [bar.is_synthetic for bar in output] == [False, False, True, True, False]
    # Synthetic bars carry forward the last observed close as OHLC.
    assert output[2].open == output[2].close == Decimal("101")
    assert output[3].open == output[3].close == Decimal("101")
    # Synthetic bars have zero volume.
    assert output[2].volume == output[3].volume == Decimal("0")
    # Real bars survive untouched.
    assert output[0].volume == output[1].volume == output[4].volume == Decimal("100")


def test_synthesizer_does_not_fill_across_session_boundary() -> None:
    """When session_id changes, do not bridge with synthetic bars."""
    bars = [
        _bar(minute=0, close="100", session="day1"),
        _bar(minute=4, close="200", session="day2"),
    ]
    output = list(BarTimeGridSynthesizer(timeframe="1m").synthesize(iter(bars)))

    assert len(output) == 2
    assert [bar.is_synthetic for bar in output] == [False, False]


def test_synthesizer_does_not_fill_leading_or_trailing_gaps() -> None:
    """Without a previous close, leading bars cannot be synthesized.

    Trailing gaps are also not filled — the synthesizer only spans
    gaps between observed bars in the same session.
    """
    bars = [
        _bar(minute=2, close="102"),
        _bar(minute=3, close="103"),
    ]
    output = list(BarTimeGridSynthesizer(timeframe="1m").synthesize(iter(bars)))

    assert [bar.start_time.minute for bar in output] == [32, 33]
    assert all(not bar.is_synthetic for bar in output)


def test_synthesizer_preserves_instrument_metadata_in_synthetic_bars() -> None:
    """Synthetic bars must carry the same instrument_id, timeframe, session_id."""
    bars = [
        _bar(minute=0, close="100"),
        _bar(minute=3, close="103"),
    ]
    output = list(BarTimeGridSynthesizer(timeframe="1m").synthesize(iter(bars)))

    synthetic = [bar for bar in output if bar.is_synthetic]
    assert len(synthetic) == 2
    for bar in synthetic:
        assert bar.instrument_id == _INSTRUMENT
        assert bar.timeframe == "1m"
        assert bar.session_id == _SESSION


def test_synthesizer_emits_half_open_intervals() -> None:
    """Each synthetic bar must have end_time = start_time + 1m."""
    bars = [_bar(minute=0, close="100"), _bar(minute=3, close="103")]
    output = list(BarTimeGridSynthesizer(timeframe="1m").synthesize(iter(bars)))

    for bar in output:
        assert bar.end_time - bar.start_time == timedelta(minutes=1)
    # Consecutive bars are contiguous: bar[i].end_time == bar[i+1].start_time
    for left, right in itertools.pairwise(output):
        assert left.end_time == right.start_time


def test_synthesizer_handles_multi_instrument_streams_per_instrument() -> None:
    """When the input interleaves instruments, gaps are filled per-instrument.

    Multi-instrument feeds keep distinct synthesis state for each
    instrument: a missing minute in AAPL must not be filled with
    data from MSFT, even when MSFT has a bar at that minute.
    """
    other = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    def make(instrument: InstrumentId, minute: int, close: str) -> Bar:
        price = Decimal(close)
        return Bar(
            instrument_id=instrument,
            start_time=start + timedelta(minutes=minute),
            end_time=start + timedelta(minutes=minute + 1),
            timeframe="1m",
            session_id=_SESSION,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=Decimal("100"),
            is_complete=True,
        )

    # AAPL has a gap at minute 1; MSFT does not.
    interleaved = [
        make(_INSTRUMENT, 0, "100"),
        make(other, 0, "200"),
        make(other, 1, "201"),
        make(_INSTRUMENT, 2, "102"),
        make(other, 2, "202"),
    ]
    output = list(BarTimeGridSynthesizer(timeframe="1m").synthesize(iter(interleaved)))

    synthetic_for_aapl = [
        bar for bar in output if bar.is_synthetic and bar.instrument_id == _INSTRUMENT
    ]
    synthetic_for_msft = [bar for bar in output if bar.is_synthetic and bar.instrument_id == other]
    assert len(synthetic_for_aapl) == 1, (
        f"AAPL should have 1 synthetic bar; got {synthetic_for_aapl}"
    )
    assert synthetic_for_aapl[0].start_time == start + timedelta(minutes=1)
    assert synthetic_for_aapl[0].close == Decimal("100")
    assert synthetic_for_msft == [], "MSFT had no gap; no synthetic bars expected"
