from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.domain.market_data import Bar


def test_replay_clock_advances_deterministically_over_ordered_events() -> None:
    from qts.backtest.replay_clock import ReplayClock

    first = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    second = first + timedelta(minutes=1)
    clock = ReplayClock([second, first])

    assert not clock.done
    assert clock.advance() == first
    assert clock.current_time == first
    assert clock.advance() == second
    assert clock.current_time == second
    assert clock.done


def test_replay_clock_returns_none_when_complete() -> None:
    from qts.backtest.replay_clock import ReplayClock

    assert ReplayClock([]).advance() is None


def _bar(instrument_id: str, start: datetime) -> Bar:
    from qts.core.ids import InstrumentId

    return Bar(
        instrument_id=InstrumentId(instrument_id),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        is_complete=True,
    )


def test_backtest_events_order_by_time_instrument_and_source_sequence() -> None:
    from qts.backtest.events import BacktestMarketDataEvent, order_backtest_events

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    si = _bar("FUTURE.CME.SI.SIN0", start)
    gc_late_sequence = _bar("FUTURE.CME.GC.GCQ0", start)
    gc_early_sequence = _bar("FUTURE.CME.GC.GCQ0", start)

    ordered = order_backtest_events(
        [
            BacktestMarketDataEvent(bar=si, source_sequence=1),
            BacktestMarketDataEvent(bar=gc_late_sequence, source_sequence=2),
            BacktestMarketDataEvent(bar=gc_early_sequence, source_sequence=0),
        ]
    )

    assert [(event.bar.instrument_id.value, event.source_sequence) for event in ordered] == [
        ("FUTURE.CME.GC.GCQ0", 0),
        ("FUTURE.CME.GC.GCQ0", 2),
        ("FUTURE.CME.SI.SIN0", 1),
    ]
