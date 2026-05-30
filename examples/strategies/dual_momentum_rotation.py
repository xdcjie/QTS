"""Dual-momentum futures rotation example using the public Strategy SDK."""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, DataView, Strategy, StrategyContext

_TRADING_DAYS_PER_YEAR = Decimal("252")


class DualMomentumRotationStrategy(Strategy):
    """Rotate into the strongest configured asset when absolute momentum is positive."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC", "SI"),
        timeframe: str = "1d",
        lookback_bars: int | Sequence[int] = 63,
        rebalance_bars: int = 21,
        min_absolute_momentum: Decimal = Decimal("0"),
        min_relative_momentum: Decimal = Decimal("0.05"),
        volatility_lookback_bars: int = 0,
        high_volatility_threshold: Decimal | None = None,
        high_volatility_confirmation_bars: int = 1,
        max_drawdown_fraction: Decimal | None = None,
        drawdown_cooldown_bars: int = 0,
        target_quantities: Mapping[str, Decimal | str | int] | None = None,
        history_buffer_bars: int = 20,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        normalized_lookbacks = _lookback_tuple(lookback_bars)
        if rebalance_bars <= 0:
            raise ValueError("rebalance_bars must be positive")
        if volatility_lookback_bars < 0:
            raise ValueError("volatility_lookback_bars must be non-negative")
        if high_volatility_confirmation_bars <= 0:
            raise ValueError("high_volatility_confirmation_bars must be positive")
        if drawdown_cooldown_bars < 0:
            raise ValueError("drawdown_cooldown_bars must be non-negative")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")
        normalized_min_absolute = Decimal(str(min_absolute_momentum))
        normalized_min_relative = Decimal(str(min_relative_momentum))
        normalized_high_volatility = (
            None if high_volatility_threshold is None else Decimal(str(high_volatility_threshold))
        )
        normalized_max_drawdown = (
            None if max_drawdown_fraction is None else Decimal(str(max_drawdown_fraction))
        )
        if normalized_min_absolute < Decimal("0"):
            raise ValueError("min_absolute_momentum must be non-negative")
        if normalized_min_relative < Decimal("0"):
            raise ValueError("min_relative_momentum must be non-negative")
        if normalized_max_drawdown is not None and not (
            Decimal("0") < normalized_max_drawdown < Decimal("1")
        ):
            raise ValueError("max_drawdown_fraction must be between 0 and 1")
        if normalized_high_volatility is not None:
            if normalized_high_volatility <= Decimal("0"):
                raise ValueError("high_volatility_threshold must be positive")
            if volatility_lookback_bars <= 1:
                raise ValueError(
                    "volatility_lookback_bars must be greater than 1 when "
                    "high_volatility_threshold is set"
                )

        quantities = {symbol: Decimal("1") for symbol in normalized_symbols}
        for symbol, quantity in (target_quantities or {}).items():
            normalized_symbol = str(symbol).strip().upper()
            if normalized_symbol not in quantities:
                raise ValueError("target_quantities must reference configured symbols")
            normalized_quantity = Decimal(str(quantity))
            if normalized_quantity <= Decimal("0"):
                raise ValueError("target quantities must be positive")
            quantities[normalized_symbol] = normalized_quantity

        self._symbols = normalized_symbols
        self._timeframe = timeframe
        self._lookback_bars = normalized_lookbacks
        self._rebalance_bars = rebalance_bars
        self._min_absolute_momentum = normalized_min_absolute
        self._min_relative_momentum = normalized_min_relative
        self._volatility_lookback_bars = volatility_lookback_bars
        self._high_volatility_threshold = normalized_high_volatility
        self._high_volatility_confirmation_bars = high_volatility_confirmation_bars
        self._max_drawdown_fraction = normalized_max_drawdown
        self._drawdown_cooldown_bars = drawdown_cooldown_bars
        self._target_quantities = quantities
        self._history_buffer_bars = history_buffer_bars
        self._assets: dict[str, AssetRef] = {}
        self._symbol_by_instrument: dict[object, str] = {}
        self._current_targets = {symbol: Decimal("0") for symbol in normalized_symbols}
        self._last_evaluated_time: object | None = None
        self._aligned_bar_count = 0
        self._last_rebalance_bar_count: int | None = None
        self._pending_signal: str | None = None
        self._pending_signal_count = 0
        self._peak_equity: Decimal | None = None
        self._drawdown_cooldown_remaining = 0

    def initialize(self, ctx: StrategyContext) -> None:
        for symbol in self._symbols:
            asset = self._asset_for_symbol(ctx, symbol)
            self._assets[symbol] = asset
            self._symbol_by_instrument[asset.instrument_id] = symbol
            ctx.subscribe(
                asset,
                timeframe=self._timeframe,
                warmup=self._required_history + self._history_buffer_bars,
            )

    @property
    def _required_history(self) -> int:
        return max(max(self._lookback_bars), self._volatility_lookback_bars) + 1

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        data = ctx.data
        if data is None or bar.instrument_id not in self._symbol_by_instrument:
            return
        histories = self._histories(data)
        if histories is None:
            return
        latest_end_time = self._aligned_end_time(histories)
        if latest_end_time is None or latest_end_time == self._last_evaluated_time:
            return
        self._last_evaluated_time = latest_end_time
        self._aligned_bar_count += 1
        if self._drawdown_risk_off(ctx):
            self._pending_signal = None
            self._pending_signal_count = 0
            self._apply_targets(ctx, None)
            return
        if (
            self._last_rebalance_bar_count is not None
            and self._aligned_bar_count - self._last_rebalance_bar_count < self._rebalance_bars
        ):
            return
        self._last_rebalance_bar_count = self._aligned_bar_count

        selected = self._confirmed_symbol(self._selected_symbol(histories), histories)
        self._apply_targets(ctx, selected)

    def _drawdown_risk_off(self, ctx: StrategyContext) -> bool:
        if self._max_drawdown_fraction is None or ctx.portfolio is None:
            return False
        equity = ctx.portfolio.equity
        if self._drawdown_cooldown_remaining > 0:
            self._drawdown_cooldown_remaining -= 1
            if self._drawdown_cooldown_remaining == 0:
                self._peak_equity = equity
            return True
        if self._peak_equity is None or equity > self._peak_equity:
            self._peak_equity = equity
        if self._peak_equity <= Decimal("0"):
            return False
        drawdown = Decimal("1") - equity / self._peak_equity
        if drawdown < self._max_drawdown_fraction:
            return False
        self._drawdown_cooldown_remaining = self._drawdown_cooldown_bars
        if self._drawdown_cooldown_remaining == 0:
            self._peak_equity = equity
        return True

    def _histories(self, data: DataView) -> dict[str, tuple[Bar, ...]] | None:
        histories: dict[str, tuple[Bar, ...]] = {}
        for symbol, asset in self._assets.items():
            history = data.history(
                asset,
                bars=self._required_history,
                timeframe=self._timeframe,
            )
            if len(history) < self._required_history:
                return None
            histories[symbol] = history
        return histories

    def _aligned_end_time(self, histories: Mapping[str, tuple[Bar, ...]]) -> object | None:
        end_times = {history[-1].end_time for history in histories.values()}
        if len(end_times) != 1:
            return None
        return next(iter(end_times))

    def _selected_symbol(self, histories: Mapping[str, tuple[Bar, ...]]) -> str | None:
        momentum = {symbol: self._momentum_score(history) for symbol, history in histories.items()}
        ranked = sorted(momentum.items(), key=lambda item: item[1], reverse=True)
        best_symbol, best_momentum = ranked[0]
        runner_up = ranked[1][1] if len(ranked) > 1 else Decimal("0")
        if (
            best_momentum > self._min_absolute_momentum
            and best_momentum - runner_up >= self._min_relative_momentum
        ):
            return best_symbol
        return None

    def _momentum_score(self, history: tuple[Bar, ...]) -> Decimal:
        scores = [
            history[-1].close / history[-1 - lookback].close - Decimal("1")
            for lookback in self._lookback_bars
        ]
        return sum(scores, Decimal("0")) / Decimal(len(scores))

    def _confirmed_symbol(
        self,
        selected: str | None,
        histories: Mapping[str, tuple[Bar, ...]],
    ) -> str | None:
        if selected is None:
            self._pending_signal = None
            self._pending_signal_count = 0
            return None
        if selected == self._pending_signal:
            self._pending_signal_count += 1
        else:
            self._pending_signal = selected
            self._pending_signal_count = 1
        required_count = self._required_confirmation_bars(selected, histories)
        if self._pending_signal_count >= required_count:
            return selected
        return self._active_symbol()

    def _required_confirmation_bars(
        self,
        selected: str,
        histories: Mapping[str, tuple[Bar, ...]],
    ) -> int:
        if self._high_volatility_threshold is None:
            return 1
        volatility = self._annualized_volatility(histories[selected])
        if volatility is not None and volatility > self._high_volatility_threshold:
            return self._high_volatility_confirmation_bars
        return 1

    def _annualized_volatility(self, history: tuple[Bar, ...]) -> Decimal | None:
        if self._volatility_lookback_bars <= 1:
            return None
        returns: list[Decimal] = []
        volatility_slice = history[-self._volatility_lookback_bars - 1 :]
        for previous, current in itertools.pairwise(volatility_slice):
            if previous.close <= Decimal("0"):
                return None
            returns.append(current.close / previous.close - Decimal("1"))
        mean = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((item - mean) ** 2 for item in returns) / Decimal(len(returns))
        return variance.sqrt() * _TRADING_DAYS_PER_YEAR.sqrt()

    def _active_symbol(self) -> str | None:
        for symbol, target in self._current_targets.items():
            if target != Decimal("0"):
                return symbol
        return None

    def _apply_targets(self, ctx: StrategyContext, selected: str | None) -> None:
        for symbol in self._symbols:
            asset = self._assets[symbol]
            target = self._target_quantities[symbol] if selected == symbol else Decimal("0")
            if target == self._current_targets[symbol]:
                continue
            if target == Decimal("0"):
                ctx.close(asset)
            else:
                ctx.target_quantity(asset, target)
            self._current_targets[symbol] = target

    def _asset_for_symbol(self, ctx: StrategyContext, symbol: str) -> AssetRef:
        try:
            return ctx.future(symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(symbol)


def _lookback_tuple(value: int | Sequence[int]) -> tuple[int, ...]:
    lookbacks: tuple[int, ...]
    lookbacks = (value,) if isinstance(value, int) else tuple(int(item) for item in value)
    if not lookbacks or any(lookback <= 0 for lookback in lookbacks):
        raise ValueError("lookback_bars must contain positive integers")
    return tuple(dict.fromkeys(lookbacks))


__all__ = ["DualMomentumRotationStrategy"]
