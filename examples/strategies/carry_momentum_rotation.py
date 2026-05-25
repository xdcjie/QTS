"""Carry- and momentum-ranked futures rotation using the public Strategy SDK."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, DataView, Strategy, StrategyContext

_TRADING_DAYS_PER_YEAR = Decimal("252")


@dataclass(frozen=True, slots=True)
class _AssetPair:
    trade: AssetRef
    carry: AssetRef


@dataclass(frozen=True, slots=True)
class _SymbolScore:
    symbol: str
    score: Decimal
    target_percent: Decimal


class CarryMomentumRotationStrategy(Strategy):
    """Hold the strongest futures trend when carry z-score confirms the ranking."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC", "SI"),
        carry_symbols: Mapping[str, str] | None = None,
        timeframe: str = "1d",
        momentum_lookback_bars: int | Sequence[int] = (21, 63, 126),
        volatility_lookback_bars: int = 40,
        carry_zscore_lookback_bars: int = 20,
        carry_zscore_weight: Decimal = Decimal("0.02"),
        min_score: Decimal = Decimal("0"),
        min_relative_score: Decimal = Decimal("0.02"),
        target_annual_vol: Decimal = Decimal("0.20"),
        max_target_percent: Decimal = Decimal("0.50"),
        rebalance_threshold: Decimal = Decimal("0.01"),
        history_buffer_bars: int = 20,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        normalized_carry_symbols = {
            str(root).strip().upper(): str(symbol).strip().upper()
            for root, symbol in (carry_symbols or {}).items()
        }
        missing_carry = [
            symbol for symbol in normalized_symbols if symbol not in normalized_carry_symbols
        ]
        if missing_carry:
            raise ValueError("carry_symbols must contain every trade symbol")
        normalized_lookbacks = self._lookback_tuple(momentum_lookback_bars)
        if volatility_lookback_bars <= 1:
            raise ValueError("volatility_lookback_bars must be greater than 1")
        if carry_zscore_lookback_bars <= 1:
            raise ValueError("carry_zscore_lookback_bars must be greater than 1")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")
        normalized_carry_weight = Decimal(str(carry_zscore_weight))
        normalized_min_score = Decimal(str(min_score))
        normalized_min_relative = Decimal(str(min_relative_score))
        normalized_target_vol = Decimal(str(target_annual_vol))
        normalized_max_target = Decimal(str(max_target_percent))
        normalized_rebalance = Decimal(str(rebalance_threshold))
        if normalized_carry_weight < Decimal("0"):
            raise ValueError("carry_zscore_weight must be non-negative")
        if normalized_min_relative < Decimal("0"):
            raise ValueError("min_relative_score must be non-negative")
        if normalized_target_vol <= Decimal("0"):
            raise ValueError("target_annual_vol must be positive")
        if normalized_max_target <= Decimal("0"):
            raise ValueError("max_target_percent must be positive")
        if normalized_rebalance < Decimal("0"):
            raise ValueError("rebalance_threshold must be non-negative")

        self._symbols = normalized_symbols
        self._carry_symbols = normalized_carry_symbols
        self._timeframe = timeframe
        self._momentum_lookback_bars = normalized_lookbacks
        self._volatility_lookback_bars = volatility_lookback_bars
        self._carry_zscore_lookback_bars = carry_zscore_lookback_bars
        self._carry_zscore_weight = normalized_carry_weight
        self._min_score = normalized_min_score
        self._min_relative_score = normalized_min_relative
        self._target_annual_vol = normalized_target_vol
        self._max_target_percent = normalized_max_target
        self._rebalance_threshold = normalized_rebalance
        self._history_buffer_bars = history_buffer_bars
        self._assets: dict[str, _AssetPair] = {}
        self._subscribed_instruments: set[object] = set()
        self._current_targets = {symbol: Decimal("0") for symbol in normalized_symbols}
        self._last_decision_time: object | None = None

    @staticmethod
    def _lookback_tuple(value: int | Sequence[int]) -> tuple[int, ...]:
        lookbacks: tuple[int, ...]
        if isinstance(value, int):
            lookbacks = (value,)
        else:
            lookbacks = tuple(int(item) for item in value)
        if not lookbacks or any(lookback <= 0 for lookback in lookbacks):
            raise ValueError("momentum_lookback_bars must contain positive integers")
        return tuple(dict.fromkeys(lookbacks))

    @property
    def _required_price_history(self) -> int:
        return max(max(self._momentum_lookback_bars) + 1, self._volatility_lookback_bars + 1)

    def initialize(self, ctx: StrategyContext) -> None:
        for symbol in self._symbols:
            trade_asset = self._asset_for_symbol(ctx, symbol)
            carry_asset = ctx.symbol(self._carry_symbols[symbol])
            self._assets[symbol] = _AssetPair(trade=trade_asset, carry=carry_asset)
            self._subscribed_instruments.add(trade_asset.instrument_id)
            self._subscribed_instruments.add(carry_asset.instrument_id)
            ctx.subscribe(
                trade_asset,
                timeframe=self._timeframe,
                warmup=self._required_price_history + self._history_buffer_bars,
            )
            ctx.subscribe(
                carry_asset,
                timeframe=self._timeframe,
                warmup=self._carry_zscore_lookback_bars + self._history_buffer_bars,
            )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if ctx.data is None or bar.instrument_id not in self._subscribed_instruments:
            return
        histories = self._histories(ctx.data)
        if histories is None:
            return
        end_time, price_histories, carry_histories = histories
        if self._last_decision_time == end_time:
            return
        self._last_decision_time = end_time

        selected = self._selected_score(
            price_histories=price_histories,
            carry_histories=carry_histories,
        )
        self._apply_targets(ctx, selected)

    def _histories(
        self,
        data: DataView,
    ) -> tuple[object, dict[str, tuple[Bar, ...]], dict[str, tuple[Bar, ...]]] | None:
        price_histories: dict[str, tuple[Bar, ...]] = {}
        carry_histories: dict[str, tuple[Bar, ...]] = {}
        end_times: set[object] = set()
        for symbol, assets in self._assets.items():
            price_history = data.history(
                assets.trade,
                bars=self._required_price_history,
                timeframe=self._timeframe,
            )
            carry_history = data.history(
                assets.carry,
                bars=self._carry_zscore_lookback_bars,
                timeframe=self._timeframe,
            )
            if (
                len(price_history) < self._required_price_history
                or len(carry_history) < self._carry_zscore_lookback_bars
            ):
                return None
            price_histories[symbol] = price_history
            carry_histories[symbol] = carry_history
            end_times.add(price_history[-1].end_time)
            end_times.add(carry_history[-1].end_time)
        if len(end_times) != 1:
            return None
        return next(iter(end_times)), price_histories, carry_histories

    def _selected_score(
        self,
        *,
        price_histories: Mapping[str, tuple[Bar, ...]],
        carry_histories: Mapping[str, tuple[Bar, ...]],
    ) -> _SymbolScore | None:
        scores = tuple(
            score
            for symbol in self._symbols
            if (
                score := self._score_for_symbol(
                    symbol,
                    price_history=price_histories[symbol],
                    carry_history=carry_histories[symbol],
                )
            )
            is not None
        )
        if not scores:
            return None
        ranked = sorted(scores, key=lambda item: item.score, reverse=True)
        best = ranked[0]
        runner_up = ranked[1].score if len(ranked) > 1 else Decimal("0")
        if best.score >= self._min_score and best.score - runner_up >= self._min_relative_score:
            return best
        return None

    def _score_for_symbol(
        self,
        symbol: str,
        *,
        price_history: tuple[Bar, ...],
        carry_history: tuple[Bar, ...],
    ) -> _SymbolScore | None:
        momentum = self._momentum_score(price_history)
        carry_zscore = self._carry_zscore(carry_history)
        annualized_vol = self._annualized_volatility(price_history)
        if carry_zscore is None or annualized_vol <= Decimal("0"):
            return None
        score = momentum + self._carry_zscore_weight * carry_zscore
        target = min(self._target_annual_vol / annualized_vol, self._max_target_percent)
        return _SymbolScore(symbol=symbol, score=score, target_percent=target)

    def _momentum_score(self, history: tuple[Bar, ...]) -> Decimal:
        scores = [
            history[-1].close / history[-1 - lookback].close - Decimal("1")
            for lookback in self._momentum_lookback_bars
        ]
        return sum(scores, Decimal("0")) / Decimal(len(scores))

    def _carry_zscore(self, history: tuple[Bar, ...]) -> Decimal | None:
        values = tuple(bar.close for bar in history)
        mean = sum(values, Decimal("0")) / Decimal(len(values))
        variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
        if variance <= Decimal("0"):
            return None
        return (values[-1] - mean) / variance.sqrt()

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

    def _apply_targets(self, ctx: StrategyContext, selected: _SymbolScore | None) -> None:
        selected_symbol = None if selected is None else selected.symbol
        for symbol in self._symbols:
            if symbol == selected_symbol:
                continue
            if self._current_targets[symbol] != Decimal("0"):
                ctx.close(self._assets[symbol].trade)
                self._current_targets[symbol] = Decimal("0")
        if selected is None:
            return
        current = self._current_targets[selected.symbol]
        if abs(selected.target_percent - current) < self._rebalance_threshold:
            return
        ctx.target_percent(self._assets[selected.symbol].trade, selected.target_percent)
        self._current_targets[selected.symbol] = selected.target_percent

    def _asset_for_symbol(self, ctx: StrategyContext, symbol: str) -> AssetRef:
        try:
            return ctx.future(symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(symbol)


__all__ = ["CarryMomentumRotationStrategy"]
