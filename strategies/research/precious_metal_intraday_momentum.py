"""GC/SI intraday first-window momentum into the close.

The strategy tests the documented intraday momentum hypothesis that the first
part of a trading session can predict the final part of the same session. It
uses only completed bars and session-local state.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


@dataclass(slots=True)
class _SessionState:
    session_id: str | None = None
    bar_count: int = 0
    open_price: Decimal | None = None
    first_window_close: Decimal | None = None
    first_window_high: Decimal | None = None
    first_window_low: Decimal | None = None
    entered: bool = False
    side: int = 0
    entry_price: Decimal | None = None
    bars_held: int = 0
    last_decision_time: object | None = None

    @property
    def first_window_range(self) -> Decimal | None:
        if self.first_window_high is None or self.first_window_low is None:
            return None
        return self.first_window_high - self.first_window_low


class PreciousMetalIntradayMomentumStrategy(Strategy):
    """Trade GC/SI in the last session segment based on first-window return."""

    def __init__(
        self,
        *,
        symbols: tuple[str, ...] = ("GC", "SI"),
        timeframe: str = "1m",
        mode: str = "momentum",
        first_window_bars: int = 30,
        entry_start_bar: int = 1320,
        entry_end_bar: int = 1350,
        force_exit_bar: int = 1376,
        min_abs_first_return: Decimal = Decimal("0.0006"),
        min_first_range_bps: Decimal = Decimal("5"),
        target_quantity: Decimal = Decimal("1"),
        atr_lookback_bars: int = 30,
        stop_atr_multiple: Decimal = Decimal("1.50"),
        take_profit_atr_multiple: Decimal = Decimal("2.50"),
        max_holding_bars: int = 90,
        allow_short: bool = True,
        history_buffer_bars: int = 5,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in {"momentum", "reversal"}:
            raise ValueError("mode must be 'momentum' or 'reversal'")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        for name, value in {
            "first_window_bars": first_window_bars,
            "entry_start_bar": entry_start_bar,
            "entry_end_bar": entry_end_bar,
            "force_exit_bar": force_exit_bar,
            "atr_lookback_bars": atr_lookback_bars,
            "max_holding_bars": max_holding_bars,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if not first_window_bars < entry_start_bar <= entry_end_bar < force_exit_bar:
            raise ValueError(
                "bar gates must satisfy first_window < entry_start <= entry_end < force_exit"
            )
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")

        self._symbols = normalized_symbols
        self._timeframe = str(timeframe)
        self._mode = normalized_mode
        self._first_window_bars = first_window_bars
        self._entry_start_bar = entry_start_bar
        self._entry_end_bar = entry_end_bar
        self._force_exit_bar = force_exit_bar
        self._min_abs_first_return = _decimal(min_abs_first_return)
        self._min_first_range_bps = _decimal(min_first_range_bps)
        self._target_quantity = _decimal(target_quantity)
        self._atr_lookback_bars = atr_lookback_bars
        self._stop_atr_multiple = _decimal(stop_atr_multiple)
        self._take_profit_atr_multiple = _decimal(take_profit_atr_multiple)
        self._max_holding_bars = max_holding_bars
        self._allow_short = allow_short
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "min_abs_first_return": self._min_abs_first_return,
            "min_first_range_bps": self._min_first_range_bps,
            "target_quantity": self._target_quantity,
            "stop_atr_multiple": self._stop_atr_multiple,
            "take_profit_atr_multiple": self._take_profit_atr_multiple,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")
        if self._stop_atr_multiple == Decimal("0"):
            raise ValueError("stop_atr_multiple must be positive")
        if self._take_profit_atr_multiple == Decimal("0"):
            raise ValueError("take_profit_atr_multiple must be positive")

        self._assets: dict[str, AssetRef] = {}
        self._instrument_to_symbol: dict[object, str] = {}
        self._state_by_symbol = {symbol: _SessionState() for symbol in normalized_symbols}

    def initialize(self, ctx: StrategyContext) -> None:
        warmup = self._atr_lookback_bars + 1 + self._history_buffer_bars
        for symbol in self._symbols:
            asset = _asset_for_symbol(ctx, symbol)
            self._assets[symbol] = asset
            self._instrument_to_symbol[asset.instrument_id] = symbol
            ctx.subscribe(asset, timeframe=self._timeframe, warmup=warmup)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        symbol = self._instrument_to_symbol.get(bar.instrument_id)
        if symbol is None:
            return
        state = self._state_by_symbol[symbol]
        if state.last_decision_time == bar.end_time:
            return
        state.last_decision_time = bar.end_time
        state = self._roll_session_if_needed(ctx, symbol, str(bar.session_id), bar)
        state.bar_count += 1
        if state.open_price is None:
            state.open_price = bar.open
        self._update_first_window(state, bar)
        if state.side != 0:
            self._manage_open_position(ctx, symbol, state, bar)
            return
        if state.entered:
            return
        if not self._in_entry_window(state):
            return
        self._evaluate_entry(ctx, symbol, state, bar)

    def _roll_session_if_needed(
        self,
        ctx: StrategyContext,
        symbol: str,
        session_id: str,
        bar: Bar,
    ) -> _SessionState:
        state = self._state_by_symbol[symbol]
        if state.session_id is None:
            state.session_id = session_id
            state.open_price = bar.open
            return state
        if state.session_id == session_id:
            return state
        if state.side != 0:
            self._close(ctx, symbol, state, reason="session_roll_flat")
        self._state_by_symbol[symbol] = _SessionState(session_id=session_id, open_price=bar.open)
        return self._state_by_symbol[symbol]

    def _update_first_window(self, state: _SessionState, bar: Bar) -> None:
        if state.bar_count > self._first_window_bars:
            return
        state.first_window_high = (
            bar.high if state.first_window_high is None else max(state.first_window_high, bar.high)
        )
        state.first_window_low = (
            bar.low if state.first_window_low is None else min(state.first_window_low, bar.low)
        )
        if state.bar_count == self._first_window_bars:
            state.first_window_close = bar.close

    def _in_entry_window(self, state: _SessionState) -> bool:
        return self._entry_start_bar <= state.bar_count <= self._entry_end_bar

    def _evaluate_entry(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SessionState,
        bar: Bar,
    ) -> None:
        if state.open_price is None or state.first_window_close is None:
            return
        if state.open_price <= Decimal("0"):
            return
        first_return = state.first_window_close / state.open_price - Decimal("1")
        if abs(first_return) < self._min_abs_first_return:
            return
        first_range = state.first_window_range
        if first_range is None:
            return
        first_range_bps = first_range / state.open_price * Decimal("10000")
        if first_range_bps < self._min_first_range_bps:
            return
        side = 1 if first_return > Decimal("0") else -1
        if self._mode == "reversal":
            side *= -1
        if side < 0 and not self._allow_short:
            state.entered = True
            return
        atr = self._atr(ctx, symbol)
        if atr is None or atr <= Decimal("0"):
            return
        self._enter(ctx, symbol, state, side=side, price=bar.close)

    def _manage_open_position(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SessionState,
        bar: Bar,
    ) -> None:
        state.bars_held += 1
        atr = self._atr(ctx, symbol)
        if atr is None or atr <= Decimal("0") or state.entry_price is None:
            return
        stop_distance = atr * self._stop_atr_multiple
        target_distance = atr * self._take_profit_atr_multiple
        if state.side > 0:
            if bar.close <= state.entry_price - stop_distance:
                self._close(ctx, symbol, state, reason="atr_stop")
            elif bar.close >= state.entry_price + target_distance:
                self._close(ctx, symbol, state, reason="atr_target")
        else:
            if bar.close >= state.entry_price + stop_distance:
                self._close(ctx, symbol, state, reason="atr_stop")
            elif bar.close <= state.entry_price - target_distance:
                self._close(ctx, symbol, state, reason="atr_target")
        if state.side == 0:
            return
        if state.bars_held >= self._max_holding_bars or state.bar_count >= self._force_exit_bar:
            self._close(ctx, symbol, state, reason="time_exit")

    def _atr(self, ctx: StrategyContext, symbol: str) -> Decimal | None:
        if ctx.data is None:
            return None
        history = ctx.data.history(
            self._assets[symbol],
            bars=self._atr_lookback_bars + 1,
            timeframe=self._timeframe,
        )
        if len(history) < self._atr_lookback_bars + 1:
            return None
        ranges: list[Decimal] = []
        for previous, current in itertools.pairwise(history[-self._atr_lookback_bars - 1 :]):
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

    def _enter(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SessionState,
        *,
        side: int,
        price: Decimal,
    ) -> None:
        quantity = self._target_quantity if side > 0 else -self._target_quantity
        ctx.target_quantity(
            self._assets[symbol],
            quantity,
            metadata={"reason": "intraday_momentum_entry", "symbol": symbol},
        )
        state.entered = True
        state.side = side
        state.entry_price = price
        state.bars_held = 0

    def _close(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _SessionState,
        *,
        reason: str,
    ) -> None:
        ctx.close(self._assets[symbol], metadata={"reason": reason, "symbol": symbol})
        state.side = 0
        state.entry_price = None
        state.bars_held = 0


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


__all__ = ["PreciousMetalIntradayMomentumStrategy"]
