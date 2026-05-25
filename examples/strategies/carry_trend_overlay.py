"""Carry-confirmed trend overlay example."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext

_TRADING_DAYS_PER_YEAR = Decimal("252")


@dataclass(frozen=True, slots=True)
class _AssetPair:
    trade: AssetRef
    carry: AssetRef


class CarryTrendOverlayStrategy(Strategy):
    """Trade futures trends only when calendar-spread carry confirms direction."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC", "SI"),
        carry_symbols: Mapping[str, str] | None = None,
        timeframe: str = "1d",
        momentum_lookback_bars: int = 126,
        volatility_lookback_bars: int = 40,
        carry_lookback_bars: int = 20,
        min_momentum_return: Decimal = Decimal("0.03"),
        min_carry: Decimal = Decimal("0"),
        target_annual_vol: Decimal = Decimal("0.15"),
        max_target_percent: Decimal = Decimal("0.40"),
        rebalance_threshold: Decimal = Decimal("0.01"),
        history_buffer_bars: int = 20,
        allow_short: bool = True,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        normalized_carry_symbols = {
            str(root).strip().upper(): str(symbol).strip().upper()
            for root, symbol in (carry_symbols or {}).items()
        }
        missing_carry = [
            symbol for symbol in normalized_symbols if symbol not in normalized_carry_symbols
        ]
        if missing_carry:
            raise ValueError("carry_symbols must contain every trade symbol")
        if momentum_lookback_bars <= 0:
            raise ValueError("momentum_lookback_bars must be positive")
        if volatility_lookback_bars <= 1:
            raise ValueError("volatility_lookback_bars must be greater than 1")
        if carry_lookback_bars <= 0:
            raise ValueError("carry_lookback_bars must be positive")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")
        normalized_min_momentum = Decimal(str(min_momentum_return))
        normalized_min_carry = Decimal(str(min_carry))
        normalized_target_annual_vol = Decimal(str(target_annual_vol))
        normalized_max_target_percent = Decimal(str(max_target_percent))
        normalized_rebalance_threshold = Decimal(str(rebalance_threshold))
        if normalized_min_momentum < Decimal("0"):
            raise ValueError("min_momentum_return must be non-negative")
        if normalized_min_carry < Decimal("0"):
            raise ValueError("min_carry must be non-negative")
        if normalized_target_annual_vol <= Decimal("0"):
            raise ValueError("target_annual_vol must be positive")
        if normalized_max_target_percent <= Decimal("0"):
            raise ValueError("max_target_percent must be positive")
        if normalized_rebalance_threshold < Decimal("0"):
            raise ValueError("rebalance_threshold must be non-negative")

        self._symbols = normalized_symbols
        self._carry_symbols = normalized_carry_symbols
        self._timeframe = timeframe
        self._momentum_lookback_bars = momentum_lookback_bars
        self._volatility_lookback_bars = volatility_lookback_bars
        self._carry_lookback_bars = carry_lookback_bars
        self._min_momentum_return = normalized_min_momentum
        self._min_carry = normalized_min_carry
        self._target_annual_vol = normalized_target_annual_vol
        self._max_target_percent = normalized_max_target_percent
        self._rebalance_threshold = normalized_rebalance_threshold
        self._history_buffer_bars = history_buffer_bars
        self._allow_short = allow_short
        self._assets: dict[str, _AssetPair] = {}
        self._symbol_by_instrument: dict[object, str] = {}
        self._current_targets = {symbol: Decimal("0") for symbol in normalized_symbols}
        self._last_decision_time: dict[str, object] = {}

    def initialize(self, ctx: StrategyContext) -> None:
        for symbol in self._symbols:
            trade_asset = self._asset_for_symbol(ctx, symbol)
            carry_asset = ctx.symbol(self._carry_symbols[symbol])
            self._assets[symbol] = _AssetPair(trade=trade_asset, carry=carry_asset)
            self._symbol_by_instrument[trade_asset.instrument_id] = symbol
            self._symbol_by_instrument[carry_asset.instrument_id] = symbol
            ctx.subscribe(
                trade_asset,
                timeframe=self._timeframe,
                warmup=self._required_price_history + self._history_buffer_bars,
            )
            ctx.subscribe(
                carry_asset,
                timeframe=self._timeframe,
                warmup=self._carry_lookback_bars + self._history_buffer_bars,
            )

    @property
    def _required_price_history(self) -> int:
        return max(self._momentum_lookback_bars, self._volatility_lookback_bars) + 1

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if ctx.data is None:
            return
        symbol = self._symbol_by_instrument.get(bar.instrument_id)
        if symbol is None:
            return
        assets = self._assets[symbol]
        price_history = ctx.data.history(
            assets.trade,
            bars=self._required_price_history,
            timeframe=self._timeframe,
        )
        carry_history = ctx.data.history(
            assets.carry,
            bars=self._carry_lookback_bars,
            timeframe=self._timeframe,
        )
        if (
            len(price_history) < self._required_price_history
            or len(carry_history) < self._carry_lookback_bars
        ):
            return
        if price_history[-1].end_time != carry_history[-1].end_time:
            return
        if self._last_decision_time.get(symbol) == price_history[-1].end_time:
            return
        self._last_decision_time[symbol] = price_history[-1].end_time

        target = self._target_for_histories(price_history, carry_history)
        if target == Decimal("0"):
            if self._current_targets[symbol] != Decimal("0"):
                ctx.close(assets.trade)
                self._current_targets[symbol] = Decimal("0")
            return
        if abs(target - self._current_targets[symbol]) < self._rebalance_threshold:
            return
        ctx.target_percent(assets.trade, target)
        self._current_targets[symbol] = target

    def _target_for_histories(
        self,
        price_history: tuple[Bar, ...],
        carry_history: tuple[Bar, ...],
    ) -> Decimal:
        momentum = price_history[-1].close / price_history[
            -1 - self._momentum_lookback_bars
        ].close - Decimal("1")
        carry_mean = sum((bar.close for bar in carry_history), Decimal("0")) / Decimal(
            len(carry_history)
        )
        carry_score = carry_history[-1].close - carry_mean
        direction = self._direction(momentum=momentum, carry_score=carry_score)
        if direction == Decimal("0"):
            return Decimal("0")
        annualized_vol = self._annualized_volatility(price_history)
        if annualized_vol <= Decimal("0"):
            return Decimal("0")
        raw_target = self._target_annual_vol / annualized_vol
        capped_target = min(raw_target, self._max_target_percent)
        return direction * capped_target

    def _direction(self, *, momentum: Decimal, carry_score: Decimal) -> Decimal:
        if momentum >= self._min_momentum_return and carry_score >= self._min_carry:
            return Decimal("1")
        if (
            self._allow_short
            and momentum <= -self._min_momentum_return
            and carry_score <= -self._min_carry
        ):
            return Decimal("-1")
        return Decimal("0")

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

    def _asset_for_symbol(self, ctx: StrategyContext, symbol: str) -> AssetRef:
        try:
            return ctx.future(symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(symbol)


__all__ = ["CarryTrendOverlayStrategy"]
