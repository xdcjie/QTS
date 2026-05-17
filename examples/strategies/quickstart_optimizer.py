"""Quickstart strategy for ``scripts/run_optimizer.py``.

Exports a ``build_strategy(params)`` factory and a ``build_bars()`` data
factory so the optimizer CLI can sweep over a small parameter grid
without users having to hand-write boilerplate. The strategy is
deliberately simple: open a fixed long target at a configurable bar
index. Different ``entry_bar`` × ``target_quantity`` combinations
produce visibly different ranked results.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


class QuickstartOptimizerStrategy(Strategy):
    """Open a single long position at a configurable bar index."""

    def __init__(self, *, entry_bar: int, target_quantity: Decimal) -> None:
        self._entry_bar = entry_bar
        self._target_quantity = target_quantity
        self._bar_index = 0
        self._opened = False
        self._asset: Any = None

    def initialize(self, ctx: Any) -> None:
        self._asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: Bar) -> None:
        self._bar_index += 1
        if self._opened or self._bar_index < self._entry_bar:
            return
        ctx.target_quantity(self._asset, self._target_quantity)
        self._opened = True


def build_strategy(params: dict[str, Any]) -> Strategy:
    """Return a fresh strategy instance for the optimizer to drive."""
    return QuickstartOptimizerStrategy(
        entry_bar=int(params["entry_bar"]),
        target_quantity=Decimal(str(params["target_quantity"])),
    )


def build_bars() -> Iterable[Bar]:
    """Return a small synthetic uptrend so different entry bars rank differently."""
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars: list[Bar] = []
    for index in range(8):
        close = Decimal(100 + index)
        bars.append(
            Bar(
                instrument_id=_INSTRUMENT,
                start_time=start + timedelta(minutes=index),
                end_time=start + timedelta(minutes=index + 1),
                timeframe="1m",
                session_id="2026-01-02",
                open=close,
                high=close,
                low=close,
                close=close,
                volume=Decimal("100"),
                is_complete=True,
            )
        )
    return bars


__all__ = ["QuickstartOptimizerStrategy", "build_bars", "build_strategy"]
