"""User-facing Strategy base class."""

from __future__ import annotations

from qts.domain.market_data import Bar, Tick
from qts.strategy_sdk.context import StrategyContext
from qts.strategy_sdk.events import Fill, OrderUpdate, TimerEvent


class Strategy:
    """Base class for user strategies."""

    def initialize(self, ctx: StrategyContext) -> None:
        """Perform initialize."""
        return None

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        """Perform on_bar."""
        return None

    def on_tick(self, ctx: StrategyContext, tick: Tick) -> None:
        """Perform on_tick."""
        return None

    def on_timer(self, ctx: StrategyContext, timer: TimerEvent) -> None:
        """Perform on_timer."""
        return None

    def on_order_update(self, ctx: StrategyContext, update: OrderUpdate) -> None:
        """Perform on_order_update."""
        return None

    def on_fill(self, ctx: StrategyContext, fill: Fill) -> None:
        """Perform on_fill."""
        return None

    def finalize(self, ctx: StrategyContext) -> None:
        """Perform finalize."""
        return None


__all__ = ["Strategy"]
