from __future__ import annotations

from datetime import UTC, datetime, timedelta


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
