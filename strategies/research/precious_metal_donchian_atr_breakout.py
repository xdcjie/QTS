"""Precious-metal Donchian breakout with ATR trailing risk control."""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext

_BPS = Decimal("10000")


@dataclass(slots=True)
class _SymbolState:
    side: int = 0
    entry_price: Decimal | None = None
    entry_atr: Decimal | None = None
    highest_close: Decimal | None = None
    bars_held: int = 0
    decision_count: int = 0
    last_counted_time: object | None = None
    last_decision_time: object | None = None


class PreciousMetalDonchianAtrBreakoutStrategy(Strategy):
    """Long-only channel breakout strategy with completed-bar decisions."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC",),
        timeframe: str = "1m",
        entry_lookback_bars: int = 4140,
        exit_lookback_bars: int = 1380,
        atr_lookback_bars: int = 120,
        decision_interval_bars: int = 60,
        breakout_buffer_bps: Decimal = Decimal("2"),
        min_atr_bps: Decimal = Decimal("4"),
        max_atr_bps: Decimal = Decimal("80"),
        target_quantity: Decimal = Decimal("1"),
        initial_stop_atr_multiple: Decimal = Decimal("3.00"),
        trailing_stop_atr_multiple: Decimal = Decimal("4.00"),
        max_holding_bars: int = 20000,
        history_buffer_bars: int = 20,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        for name, value in {
            "entry_lookback_bars": entry_lookback_bars,
            "exit_lookback_bars": exit_lookback_bars,
            "atr_lookback_bars": atr_lookback_bars,
            "decision_interval_bars": decision_interval_bars,
            "max_holding_bars": max_holding_bars,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if entry_lookback_bars <= exit_lookback_bars:
            raise ValueError("entry_lookback_bars must be greater than exit_lookback_bars")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")

        self._symbols = normalized_symbols
        self._timeframe = str(timeframe)
        self._entry_lookback_bars = entry_lookback_bars
        self._exit_lookback_bars = exit_lookback_bars
        self._atr_lookback_bars = atr_lookback_bars
        self._decision_interval_bars = decision_interval_bars
        self._breakout_buffer_bps = _decimal(breakout_buffer_bps)
        self._min_atr_bps = _decimal(min_atr_bps)
        self._max_atr_bps = _decimal(max_atr_bps)
        self._target_quantity = _decimal(target_quantity)
        self._initial_stop_atr_multiple = _decimal(initial_stop_atr_multiple)
        self._trailing_stop_atr_multiple = _decimal(trailing_stop_atr_multiple)
        self._max_holding_bars = max_holding_bars
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "breakout_buffer_bps": self._breakout_buffer_bps,
            "min_atr_bps": self._min_atr_bps,
            "max_atr_bps": self._max_atr_bps,
            "target_quantity": self._target_quantity,
            "initial_stop_atr_multiple": self._initial_stop_atr_multiple,
            "trailing_stop_atr_multiple": self._trailing_stop_atr_multiple,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._min_atr_bps > self._max_atr_bps:
            raise ValueError("min_atr_bps must be <= max_atr_bps")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")
        if self._initial_stop_atr_multiple == Decimal("0"):
            raise ValueError("initial_stop_atr_multiple must be positive")
        if self._trailing_stop_atr_multiple == Decimal("0"):
            raise ValueError("trailing_stop_atr_multiple must be positive")

        self._assets: dict[str, AssetRef] = {}
        self._instrument_to_symbol: dict[object, str] = {}
        self._state_by_symbol = {symbol: _SymbolState() for symbol in normalized_symbols}

    @property
    def _required_history(self) -> int:
        return max(self._entry_lookback_bars + 1, self._atr_lookback_bars + 1)

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
        symbol = self._instrument_to_symbol.get(bar.instrument_id)
        if symbol is None or ctx.data is None:
            return
        state = self._state_by_symbol[symbol]
        if bar.end_time != state.last_counted_time:
            state.last_counted_time = bar.end_time
            state.decision_count += 1
        if state.side != 0:
            self._manage_open_position(ctx, symbol, state, bar)
        if state.decision_count % self._decision_interval_bars != 0:
            return
        if state.last_decision_time == bar.end_time:
            return
        history = ctx.data.history(
            self._assets[symbol],
            bars=self._required_history,
            timeframe=self._timeframe,
        )
        if len(history) < self._required_history:
            return
        state.last_decision_time = bar.end_time
        if state.side == 0:
            self._evaluate_entry(ctx, symbol, state, history)
        else:
            self._evaluate_channel_exit(ctx, symbol, state, history)

    def _evaluate_entry(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SymbolState,
        history: tuple[Bar, ...],
    ) -> None:
        latest = history[-1]
        previous = history[:-1]
        if latest.close <= Decimal("0") or not previous:
            return
        entry_slice = previous[-self._entry_lookback_bars :]
        breakout_level = max(bar.high for bar in entry_slice)
        buffered_level = breakout_level * (Decimal("1") + self._breakout_buffer_bps / _BPS)
        if latest.close <= buffered_level:
            return
        atr = _atr(history[-self._atr_lookback_bars - 1 :])
        if atr is None or atr <= Decimal("0"):
            return
        atr_bps = atr / latest.close * _BPS
        if atr_bps < self._min_atr_bps or atr_bps > self._max_atr_bps:
            return
        ctx.target_quantity(
            self._assets[symbol],
            self._target_quantity,
            metadata={"reason": "donchian_breakout_entry", "symbol": symbol},
        )
        state.side = 1
        state.entry_price = latest.close
        state.entry_atr = atr
        state.highest_close = latest.close
        state.bars_held = 0

    def _evaluate_channel_exit(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SymbolState,
        history: tuple[Bar, ...],
    ) -> None:
        latest = history[-1]
        previous = history[:-1]
        if len(previous) < self._exit_lookback_bars:
            return
        exit_level = min(bar.low for bar in previous[-self._exit_lookback_bars :])
        if latest.close < exit_level:
            self._close(ctx, symbol, state, reason="donchian_channel_exit")

    def _manage_open_position(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SymbolState,
        bar: Bar,
    ) -> None:
        state.bars_held += 1
        state.highest_close = (
            bar.close if state.highest_close is None else max(state.highest_close, bar.close)
        )
        if state.entry_price is None or state.entry_atr is None:
            return
        initial_stop = state.entry_price - state.entry_atr * self._initial_stop_atr_multiple
        trailing_stop = state.highest_close - state.entry_atr * self._trailing_stop_atr_multiple
        stop = max(initial_stop, trailing_stop)
        if bar.close <= stop:
            self._close(ctx, symbol, state, reason="atr_trailing_stop")
            return
        if state.bars_held >= self._max_holding_bars:
            self._close(ctx, symbol, state, reason="max_holding_exit")

    def _close(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SymbolState,
        *,
        reason: str,
    ) -> None:
        ctx.close(self._assets[symbol], metadata={"reason": reason, "symbol": symbol})
        state.side = 0
        state.entry_price = None
        state.entry_atr = None
        state.highest_close = None
        state.bars_held = 0


def _atr(history: tuple[Bar, ...]) -> Decimal | None:
    ranges: list[Decimal] = []
    for previous, current in itertools.pairwise(history):
        ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    if not ranges:
        return None
    return sum(ranges, Decimal("0")) / Decimal(len(ranges))


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


__all__ = ["PreciousMetalDonchianAtrBreakoutStrategy"]
