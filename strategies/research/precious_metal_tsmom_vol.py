"""GC/SI time-series momentum with volatility-scaled targets.

The hypothesis follows the commodity futures time-series momentum literature:
multi-horizon past returns can persist, but position size must be constrained by
realized volatility and aggregate exposure.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, DataView, Strategy, StrategyContext

_BARS_PER_YEAR_1M = Decimal("347760")


class PreciousMetalTsmomVolStrategy(Strategy):
    """Multi-horizon GC/SI trend strategy using completed bars only."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC", "SI"),
        timeframe: str = "1m",
        momentum_lookback_bars: int | Sequence[int] = (390, 1380, 4140),
        volatility_lookback_bars: int = 1380,
        rebalance_interval_bars: int = 60,
        min_abs_score: Decimal = Decimal("0.0020"),
        full_signal_score: Decimal = Decimal("0.0200"),
        target_annual_vol: Decimal = Decimal("0.30"),
        max_target_percent: Decimal = Decimal("0.75"),
        max_total_abs_target: Decimal = Decimal("1.25"),
        target_quantity: Decimal = Decimal("1"),
        rebalance_threshold: Decimal = Decimal("0.02"),
        allow_short: bool = True,
        history_buffer_bars: int = 20,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        self._momentum_lookbacks = self._lookback_tuple(momentum_lookback_bars)
        for name, value in {
            "volatility_lookback_bars": volatility_lookback_bars,
            "rebalance_interval_bars": rebalance_interval_bars,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")

        self._symbols = normalized_symbols
        self._timeframe = str(timeframe)
        self._volatility_lookback_bars = volatility_lookback_bars
        self._rebalance_interval_bars = rebalance_interval_bars
        self._min_abs_score = _decimal(min_abs_score)
        self._full_signal_score = _decimal(full_signal_score)
        self._target_annual_vol = _decimal(target_annual_vol)
        self._max_target_percent = _decimal(max_target_percent)
        self._max_total_abs_target = _decimal(max_total_abs_target)
        self._target_quantity = _decimal(target_quantity)
        self._rebalance_threshold = _decimal(rebalance_threshold)
        self._allow_short = allow_short
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "min_abs_score": self._min_abs_score,
            "full_signal_score": self._full_signal_score,
            "target_annual_vol": self._target_annual_vol,
            "max_target_percent": self._max_target_percent,
            "max_total_abs_target": self._max_total_abs_target,
            "target_quantity": self._target_quantity,
            "rebalance_threshold": self._rebalance_threshold,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._full_signal_score <= self._min_abs_score:
            raise ValueError("full_signal_score must be greater than min_abs_score")
        if self._target_annual_vol == Decimal("0"):
            raise ValueError("target_annual_vol must be positive")
        if self._max_target_percent == Decimal("0"):
            raise ValueError("max_target_percent must be positive")
        if self._max_total_abs_target == Decimal("0"):
            raise ValueError("max_total_abs_target must be positive")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")

        self._assets: dict[str, AssetRef] = {}
        self._instrument_to_symbol: dict[object, str] = {}
        self._current_targets = {symbol: Decimal("0") for symbol in normalized_symbols}
        self._last_decision_time: object | None = None
        self._last_counted_time: object | None = None
        self._decision_count = 0

    @staticmethod
    def _lookback_tuple(value: int | Sequence[int]) -> tuple[int, ...]:
        lookbacks = (value,) if isinstance(value, int) else tuple(int(item) for item in value)
        if not lookbacks or any(lookback <= 0 for lookback in lookbacks):
            raise ValueError("momentum_lookback_bars must contain positive integers")
        return tuple(dict.fromkeys(lookbacks))

    @property
    def _required_history(self) -> int:
        return max(max(self._momentum_lookbacks) + 1, self._volatility_lookback_bars + 1)

    def initialize(self, ctx: StrategyContext) -> None:
        for symbol in self._symbols:
            asset = _asset_for_symbol(ctx, symbol)
            self._assets[symbol] = asset
            self._instrument_to_symbol[asset.instrument_id] = symbol
            ctx.subscribe(
                asset,
                timeframe=self._timeframe,
                warmup=self._required_history + self._history_buffer_bars,
            )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if ctx.data is None or bar.instrument_id not in self._instrument_to_symbol:
            return
        if bar.end_time != self._last_counted_time:
            self._last_counted_time = bar.end_time
            self._decision_count += 1
        if self._decision_count % self._rebalance_interval_bars != 0:
            return
        histories = self._histories(ctx.data)
        if histories is None:
            return
        end_time, price_histories = histories
        if end_time == self._last_decision_time:
            return
        self._last_decision_time = end_time
        targets = self._targets(price_histories)
        self._apply_targets(ctx, targets)

    def _histories(self, data: DataView) -> tuple[object, dict[str, tuple[Bar, ...]]] | None:
        histories: dict[str, tuple[Bar, ...]] = {}
        end_times: set[object] = set()
        for symbol, asset in self._assets.items():
            history = data.history(asset, bars=self._required_history, timeframe=self._timeframe)
            if len(history) < self._required_history:
                return None
            histories[symbol] = history
            end_times.add(history[-1].end_time)
        if len(end_times) != 1:
            return None
        return next(iter(end_times)), histories

    def _targets(self, histories: dict[str, tuple[Bar, ...]]) -> dict[str, Decimal]:
        raw_targets: dict[str, Decimal] = {}
        for symbol, history in histories.items():
            score = self._momentum_score(history)
            annualized_vol = self._annualized_volatility(history)
            raw_targets[symbol] = self._target_for_score(score, annualized_vol)
        total_abs = sum((abs(target) for target in raw_targets.values()), Decimal("0"))
        if total_abs <= self._max_total_abs_target:
            return raw_targets
        scale = self._max_total_abs_target / total_abs
        return {symbol: target * scale for symbol, target in raw_targets.items()}

    def _target_for_score(self, score: Decimal, annualized_vol: Decimal) -> Decimal:
        if annualized_vol <= Decimal("0") or abs(score) < self._min_abs_score:
            return Decimal("0")
        if score < Decimal("0") and not self._allow_short:
            return Decimal("0")
        direction = Decimal("1") if score > Decimal("0") else Decimal("-1")
        signal_scale = min(abs(score) / self._full_signal_score, Decimal("1"))
        if signal_scale < Decimal("1"):
            return Decimal("0")
        return direction * self._target_quantity

    def _momentum_score(self, history: tuple[Bar, ...]) -> Decimal:
        scores = [
            history[-1].close / history[-1 - lookback].close - Decimal("1")
            for lookback in self._momentum_lookbacks
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
        return variance.sqrt() * _BARS_PER_YEAR_1M.sqrt()

    def _apply_targets(self, ctx: StrategyContext, targets: dict[str, Decimal]) -> None:
        for symbol, target in targets.items():
            current = self._current_targets[symbol]
            if abs(target - current) < self._rebalance_threshold:
                continue
            asset = self._assets[symbol]
            if target == Decimal("0"):
                ctx.close(asset, metadata={"reason": "tsmom_neutral", "symbol": symbol})
            else:
                ctx.target_quantity(
                    asset,
                    target,
                    metadata={"reason": "tsmom_vol_target", "symbol": symbol},
                )
            self._current_targets[symbol] = target


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


__all__ = ["PreciousMetalTsmomVolStrategy"]
