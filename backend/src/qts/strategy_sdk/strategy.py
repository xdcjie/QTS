"""User-facing Strategy base class."""

from __future__ import annotations

from qts.domain.market_data import Bar, Tick
from qts.strategy_sdk.context import StrategyContext
from qts.strategy_sdk.events import Fill, OrderUpdate, TimerEvent


class Strategy:
    """Base class for user strategies."""

    def initialize(self, ctx: StrategyContext) -> None:
        """Set up strategy state once before any market events; no-op by default."""
        return None

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        """Handle a completed bar; override to react to bar updates."""
        return None

    def on_tick(self, ctx: StrategyContext, tick: Tick) -> None:
        """Handle an incoming tick; override to react to tick updates."""
        return None

    def on_timer(self, ctx: StrategyContext, timer: TimerEvent) -> None:
        """Handle a scheduled timer event; override to act on timers."""
        return None

    def on_order_update(self, ctx: StrategyContext, update: OrderUpdate) -> None:
        """Handle an order status change; override to track order lifecycle."""
        return None

    def on_fill(self, ctx: StrategyContext, fill: Fill) -> None:
        """Handle a trade fill; override to react to executions."""
        return None

    def finalize(self, ctx: StrategyContext) -> None:
        """Tear down strategy state after the run ends; no-op by default."""
        return None


__all__ = ["Strategy"]
