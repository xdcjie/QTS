"""Multi-timeframe momentum example using the public Strategy SDK only."""

from __future__ import annotations

from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


class MultiTimeframeMomentumStrategy(Strategy):
    """Compare short 1m momentum with a slower 5m confirmation stream."""

    def __init__(
        self,
        *,
        symbol: str = "AAPL",
        fast_bars: int = 3,
        slow_bars: int = 3,
        target_weight: Decimal = Decimal("0.25"),
    ) -> None:
        if fast_bars <= 0:
            raise ValueError("fast_bars must be positive")
        if slow_bars <= 0:
            raise ValueError("slow_bars must be positive")
        self._symbol = symbol
        self._fast_bars = fast_bars
        self._slow_bars = slow_bars
        self._target_weight = target_weight
        self._asset: AssetRef | None = None

    def initialize(self, ctx: StrategyContext) -> None:
        asset = ctx.symbol(self._symbol)
        self._asset = asset
        ctx.subscribe(asset, timeframe="1m", warmup=self._fast_bars)
        ctx.subscribe(asset, timeframe="5m", warmup=self._slow_bars)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if (
            self._asset is None
            or ctx.data is None
            or bar.instrument_id != self._asset.instrument_id
        ):
            return
        fast_history = ctx.data.history(self._asset, bars=self._fast_bars, timeframe="1m")
        slow_history = ctx.data.history(self._asset, bars=self._slow_bars, timeframe="5m")
        if len(fast_history) < self._fast_bars or len(slow_history) < self._slow_bars:
            return

        fast_momentum = fast_history[-1].close - fast_history[0].close
        slow_momentum = slow_history[-1].close - slow_history[0].close
        if fast_momentum > Decimal("0") and slow_momentum > Decimal("0"):
            ctx.target_percent(self._asset, self._target_weight)
            return
        ctx.close(self._asset)


__all__ = ["MultiTimeframeMomentumStrategy"]
