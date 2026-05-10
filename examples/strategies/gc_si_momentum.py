"""GC/SI moving-average example using only the public Strategy SDK."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


class GcSiMomentumStrategy(Strategy):
    """Simple moving-average momentum strategy for configured GC/SI symbols."""

    def __init__(
        self,
        *,
        symbols: Iterable[str] = ("GCQ0", "SIN0"),
        short_window: int = 1,
        long_window: int = 2,
    ) -> None:
        if short_window <= 0:
            raise ValueError("short_window must be positive")
        if long_window <= 0:
            raise ValueError("long_window must be positive")
        if short_window > long_window:
            raise ValueError("short_window must be less than or equal to long_window")
        self._symbols = tuple(symbols)
        self._short_window = short_window
        self._long_window = long_window
        self._assets: tuple[AssetRef, ...] = ()

    def initialize(self, ctx: StrategyContext) -> None:
        self._assets = tuple(ctx.symbol(symbol) for symbol in self._symbols)
        for asset in self._assets:
            ctx.subscribe(asset, timeframe="1m", warmup=self._long_window)

    def on_bar(self, ctx: Any, bar: object) -> None:
        if ctx.data is None:
            return
        for asset in self._assets:
            history = ctx.data.history(asset, bars=self._long_window, timeframe="1m")
            if len(history) < self._long_window:
                continue
            short_prices = [item.close for item in history[-self._short_window :]]
            long_prices = [item.close for item in history]
            short_average = _average(short_prices)
            long_average = _average(long_prices)
            if short_average > long_average:
                ctx.target_quantity(asset, Decimal("1"))
            else:
                ctx.close(asset)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    return sum(items, Decimal("0")) / Decimal(len(items))


__all__ = ["GcSiMomentumStrategy"]
