"""Daily volatility-targeted time-series momentum example."""

from __future__ import annotations

from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext

_TRADING_DAYS_PER_YEAR = Decimal("252")


class VolTargetTrendStrategy(Strategy):
    """Slow trend strategy using completed daily bars and volatility target sizing."""

    def __init__(
        self,
        *,
        symbol: str = "SI",
        timeframe: str = "1d",
        momentum_lookback_bars: int = 63,
        volatility_lookback_bars: int = 20,
        target_annual_vol: Decimal = Decimal("0.20"),
        max_target_percent: Decimal = Decimal("0.50"),
        min_signal_return: Decimal = Decimal("0.03"),
        rebalance_threshold: Decimal = Decimal("0.01"),
        allow_short: bool = True,
    ) -> None:
        if momentum_lookback_bars <= 0:
            raise ValueError("momentum_lookback_bars must be positive")
        if volatility_lookback_bars <= 1:
            raise ValueError("volatility_lookback_bars must be greater than 1")
        normalized_target_annual_vol = Decimal(str(target_annual_vol))
        normalized_max_target_percent = Decimal(str(max_target_percent))
        normalized_min_signal_return = Decimal(str(min_signal_return))
        normalized_rebalance_threshold = Decimal(str(rebalance_threshold))
        if normalized_target_annual_vol <= Decimal("0"):
            raise ValueError("target_annual_vol must be positive")
        if normalized_max_target_percent <= Decimal("0"):
            raise ValueError("max_target_percent must be positive")
        if normalized_min_signal_return < Decimal("0"):
            raise ValueError("min_signal_return must be non-negative")
        if normalized_rebalance_threshold < Decimal("0"):
            raise ValueError("rebalance_threshold must be non-negative")
        self._symbol = symbol
        self._timeframe = timeframe
        self._momentum_lookback_bars = momentum_lookback_bars
        self._volatility_lookback_bars = volatility_lookback_bars
        self._target_annual_vol = normalized_target_annual_vol
        self._max_target_percent = normalized_max_target_percent
        self._min_signal_return = normalized_min_signal_return
        self._rebalance_threshold = normalized_rebalance_threshold
        self._allow_short = allow_short
        self._asset: AssetRef | None = None
        self._current_target = Decimal("0")

    def initialize(self, ctx: StrategyContext) -> None:
        self._asset = self._asset_for_symbol(ctx)
        ctx.subscribe(self._asset, timeframe=self._timeframe, warmup=self._required_history)

    @property
    def _required_history(self) -> int:
        return max(self._momentum_lookback_bars, self._volatility_lookback_bars) + 1

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if (
            self._asset is None
            or ctx.data is None
            or bar.instrument_id != self._asset.instrument_id
        ):
            return
        history = ctx.data.history(
            self._asset,
            bars=self._required_history,
            timeframe=self._timeframe,
        )
        if len(history) < self._required_history:
            return
        target = self._target_for_history(history)
        if target == Decimal("0"):
            if self._current_target != Decimal("0"):
                ctx.close(self._asset)
                self._current_target = Decimal("0")
            return
        if abs(target - self._current_target) < self._rebalance_threshold:
            return
        ctx.target_percent(self._asset, target)
        self._current_target = target

    def _asset_for_symbol(self, ctx: StrategyContext) -> AssetRef:
        try:
            return ctx.future(self._symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(self._symbol)

    def _target_for_history(self, history: tuple[Bar, ...]) -> Decimal:
        momentum = history[-1].close / history[-1 - self._momentum_lookback_bars].close - Decimal(
            "1"
        )
        if abs(momentum) < self._min_signal_return:
            return Decimal("0")
        direction = Decimal("1") if momentum > Decimal("0") else Decimal("-1")
        if direction < Decimal("0") and not self._allow_short:
            return Decimal("0")
        annualized_vol = self._annualized_volatility(history)
        if annualized_vol <= Decimal("0"):
            return Decimal("0")
        raw_target = self._target_annual_vol / annualized_vol
        capped_target = min(raw_target, self._max_target_percent)
        return direction * capped_target

    def _annualized_volatility(self, history: tuple[Bar, ...]) -> Decimal:
        returns: list[Decimal] = []
        volatility_slice = history[-self._volatility_lookback_bars - 1 :]
        for previous, current in zip(volatility_slice, volatility_slice[1:], strict=False):
            if previous.close <= Decimal("0"):
                return Decimal("0")
            returns.append(current.close / previous.close - Decimal("1"))
        mean = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((item - mean) ** 2 for item in returns) / Decimal(len(returns))
        return variance.sqrt() * _TRADING_DAYS_PER_YEAR.sqrt()


__all__ = ["VolTargetTrendStrategy"]
