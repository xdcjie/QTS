"""Deterministic backtest event ordering."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from qts.domain.market_data import Bar


@dataclass(frozen=True, slots=True)
class BacktestMarketDataEvent:
    """One replayable market data event."""

    bar: Bar
    source_sequence: int

    def __post_init__(self) -> None:
        if self.source_sequence < 0:
            raise ValueError("source_sequence must be non-negative")


def order_backtest_events(
    events: Iterable[BacktestMarketDataEvent],
) -> tuple[BacktestMarketDataEvent, ...]:
    """Order replay events by time, instrument identity, and source sequence."""

    return tuple(
        sorted(
            events,
            key=lambda event: (
                event.bar.end_time,
                event.bar.instrument_id.value,
                event.source_sequence,
            ),
        )
    )


__all__ = ["BacktestMarketDataEvent", "order_backtest_events"]
