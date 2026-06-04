"""Research-only volatility-targeted time-series momentum strategy."""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext

_TRADING_DAYS_PER_YEAR = Decimal("252")


class VolTargetTrendStrategy(Strategy):
    """Single-asset trend strategy with realized-volatility target sizing."""

    def __init__(
        self,
        *,
        symbol: str = "GC",
        timeframe: str = "1d",
        momentum_lookback_bars: int | Sequence[int] = (21, 63, 126),
        volatility_lookback_bars: int = 40,
        target_annual_vol: Decimal = Decimal("0.12"),
        max_target_percent: Decimal = Decimal("0.25"),
        min_signal_return: Decimal = Decimal("0.02"),
        rebalance_threshold: Decimal = Decimal("0.01"),
        allow_short: bool = True,
    ) -> None:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        lookbacks = _lookback_tuple(momentum_lookback_bars)
        if volatility_lookback_bars <= 1:
            raise ValueError("volatility_lookback_bars must be greater than 1")
        normalized_target_vol = Decimal(str(target_annual_vol))
        normalized_max_target = Decimal(str(max_target_percent))
        normalized_min_signal = Decimal(str(min_signal_return))
        normalized_rebalance = Decimal(str(rebalance_threshold))
        if normalized_target_vol <= Decimal("0"):
            raise ValueError("target_annual_vol must be positive")
        if normalized_max_target <= Decimal("0"):
            raise ValueError("max_target_percent must be positive")
        if normalized_min_signal < Decimal("0"):
            raise ValueError("min_signal_return must be non-negative")
        if normalized_rebalance < Decimal("0"):
            raise ValueError("rebalance_threshold must be non-negative")
        if not isinstance(allow_short, bool):
            raise ValueError("allow_short must be a bool")

        self._symbol = normalized_symbol
        self._timeframe = str(timeframe)
        self._momentum_lookback_bars = lookbacks
        self._volatility_lookback_bars = volatility_lookback_bars
        self._target_annual_vol = normalized_target_vol
        self._max_target_percent = normalized_max_target
        self._min_signal_return = normalized_min_signal
        self._rebalance_threshold = normalized_rebalance
        self._allow_short = allow_short
        self._asset: AssetRef | None = None
        self._current_target = Decimal("0")

    @property
    def _required_history(self) -> int:
        return max(max(self._momentum_lookback_bars), self._volatility_lookback_bars) + 1

    def initialize(self, ctx: StrategyContext) -> None:
        self._asset = self._asset_for_symbol(ctx, self._symbol)
        ctx.subscribe(self._asset, timeframe=self._timeframe, warmup=self._required_history)

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

    def _target_for_history(self, history: tuple[Bar, ...]) -> Decimal:
        momentum = self._momentum_score(history)
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

    def _momentum_score(self, history: tuple[Bar, ...]) -> Decimal:
        scores = [
            history[-1].close / history[-1 - lookback].close - Decimal("1")
            for lookback in self._momentum_lookback_bars
            if history[-1 - lookback].close > Decimal("0")
        ]
        if not scores:
            return Decimal("0")
        return sum(scores, Decimal("0")) / Decimal(len(scores))

    def _annualized_volatility(self, history: tuple[Bar, ...]) -> Decimal:
        returns: list[Decimal] = []
        volatility_slice = history[-self._volatility_lookback_bars - 1 :]
        for previous, current in itertools.pairwise(volatility_slice):
            if previous.close <= Decimal("0"):
                return Decimal("0")
            returns.append(current.close / previous.close - Decimal("1"))
        if not returns:
            return Decimal("0")
        mean = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((item - mean) ** 2 for item in returns) / Decimal(len(returns))
        return variance.sqrt() * _TRADING_DAYS_PER_YEAR.sqrt()

    @staticmethod
    def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
        try:
            return ctx.future(symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(symbol)


def _lookback_tuple(value: int | Sequence[int]) -> tuple[int, ...]:
    lookbacks = (value,) if isinstance(value, int) else tuple(int(item) for item in value)
    if not lookbacks or any(lookback <= 0 for lookback in lookbacks):
        raise ValueError("momentum_lookback_bars must contain positive integers")
    return tuple(dict.fromkeys(lookbacks))


__all__ = ["VolTargetTrendStrategy"]
