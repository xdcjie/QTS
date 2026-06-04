"""Low-frequency moving-average trend filter for precious-metal futures."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext

_BPS = Decimal("10000")


@dataclass(slots=True)
class _TrendState:
    invested: bool = False
    bars_held: int = 0
    cooldown_remaining: int = 0
    decision_count: int = 0
    last_counted_time: object | None = None
    last_decision_time: object | None = None


class PreciousMetalMaTrendFilterStrategy(Strategy):
    """Long/flat MA trend strategy with hysteresis and cooldown."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC",),
        timeframe: str = "1m",
        short_window: int = 60,
        long_window: int = 240,
        decision_interval_bars: int = 30,
        entry_spread_bps: Decimal = Decimal("4"),
        exit_spread_bps: Decimal = Decimal("0"),
        target_quantity: Decimal = Decimal("1"),
        min_holding_bars: int = 120,
        max_holding_bars: int = 20000,
        cooldown_bars: int = 120,
        history_buffer_bars: int = 5,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        for name, value in {
            "short_window": short_window,
            "long_window": long_window,
            "decision_interval_bars": decision_interval_bars,
            "min_holding_bars": min_holding_bars,
            "max_holding_bars": max_holding_bars,
            "cooldown_bars": cooldown_bars,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if short_window > long_window:
            raise ValueError("short_window must be <= long_window")
        if min_holding_bars > max_holding_bars:
            raise ValueError("min_holding_bars must be <= max_holding_bars")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")

        self._symbols = normalized_symbols
        self._timeframe = str(timeframe)
        self._short_window = short_window
        self._long_window = long_window
        self._decision_interval_bars = decision_interval_bars
        self._entry_spread_bps = _decimal(entry_spread_bps)
        self._exit_spread_bps = _decimal(exit_spread_bps)
        self._target_quantity = _decimal(target_quantity)
        self._min_holding_bars = min_holding_bars
        self._max_holding_bars = max_holding_bars
        self._cooldown_bars = cooldown_bars
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "entry_spread_bps": self._entry_spread_bps,
            "exit_spread_bps": self._exit_spread_bps,
            "target_quantity": self._target_quantity,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")

        self._assets: dict[str, AssetRef] = {}
        self._instrument_to_symbol: dict[object, str] = {}
        self._state_by_symbol = {symbol: _TrendState() for symbol in normalized_symbols}

    def initialize(self, ctx: StrategyContext) -> None:
        for symbol in self._symbols:
            asset = _asset_for_symbol(ctx, symbol)
            self._assets[symbol] = asset
            self._instrument_to_symbol[asset.instrument_id] = symbol
            ctx.subscribe(
                asset,
                timeframe=self._timeframe,
                warmup=self._long_window + self._history_buffer_bars,
            )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        symbol = self._instrument_to_symbol.get(bar.instrument_id)
        if symbol is None or ctx.data is None:
            return
        state = self._state_by_symbol[symbol]
        if bar.end_time != state.last_counted_time:
            state.last_counted_time = bar.end_time
            state.decision_count += 1
            if state.invested:
                state.bars_held += 1
            elif state.cooldown_remaining > 0:
                state.cooldown_remaining -= 1
        if state.decision_count % self._decision_interval_bars != 0:
            return
        if state.last_decision_time == bar.end_time:
            return
        history = ctx.data.history(
            self._assets[symbol],
            bars=self._long_window,
            timeframe=self._timeframe,
        )
        if len(history) < self._long_window:
            return
        state.last_decision_time = bar.end_time
        short_average = _average(bar.close for bar in history[-self._short_window :])
        long_average = _average(bar.close for bar in history)
        if long_average <= Decimal("0"):
            return
        spread_bps = (short_average / long_average - Decimal("1")) * _BPS
        if state.invested:
            self._evaluate_exit(ctx, symbol, state, spread_bps)
        else:
            self._evaluate_entry(ctx, symbol, state, spread_bps)

    def _evaluate_entry(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _TrendState,
        spread_bps: Decimal,
    ) -> None:
        if state.cooldown_remaining > 0:
            return
        if spread_bps < self._entry_spread_bps:
            return
        ctx.target_quantity(
            self._assets[symbol],
            self._target_quantity,
            metadata={"reason": "ma_trend_entry", "symbol": symbol},
        )
        state.invested = True
        state.bars_held = 0

    def _evaluate_exit(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _TrendState,
        spread_bps: Decimal,
    ) -> None:
        if state.bars_held >= self._max_holding_bars:
            self._close(ctx, symbol, state, reason="max_holding_exit")
            return
        if state.bars_held < self._min_holding_bars:
            return
        if spread_bps <= self._exit_spread_bps:
            self._close(ctx, symbol, state, reason="ma_trend_exit")

    def _close(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _TrendState,
        *,
        reason: str,
    ) -> None:
        ctx.close(self._assets[symbol], metadata={"reason": reason, "symbol": symbol})
        state.invested = False
        state.bars_held = 0
        state.cooldown_remaining = self._cooldown_bars


def _average(values: object) -> Decimal:
    items = tuple(values)
    return sum(items, Decimal("0")) / Decimal(len(items))


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


__all__ = ["PreciousMetalMaTrendFilterStrategy"]
