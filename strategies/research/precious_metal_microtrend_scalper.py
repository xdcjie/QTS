"""Precious-metal micro-trend scalper using only the public QTS Strategy SDK.

Research provenance: intraday momentum and risk-aware scalping are common public
research themes. This implementation is deliberately simple, deterministic, and
bar-based so it can pass through QTS backtest/paper/live boundaries without
accessing market-data adapters, brokers, risk internals, or future bars.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext

_BPS = Decimal("10000")


class PreciousMetalMicrotrendScalperStrategy(Strategy):
    """1m/5m momentum scalper for liquid precious-metal futures.

    Entry idea:
    - short-window and slow-window returns agree;
    - latest price is on the same side of rolling VWAP;
    - latest volume is above recent average;
    - price is not too far from VWAP, avoiding late/chasing entries.

    Exit idea:
    - ATR stop;
    - ATR take-profit;
    - maximum holding bars.
    """

    def __init__(
        self,
        *,
        symbol: str = "GC",
        timeframe: str = "1m",
        fast_bars: int = 3,
        slow_bars: int = 12,
        vwap_lookback_bars: int = 30,
        volume_lookback_bars: int = 20,
        atr_lookback_bars: int = 14,
        entry_return_threshold: Decimal = Decimal("0.0002"),
        min_volume_ratio: Decimal = Decimal("1.20"),
        max_vwap_distance_bps: Decimal = Decimal("40"),
        target_quantity: Decimal = Decimal("1"),
        stop_atr_multiple: Decimal = Decimal("1.20"),
        take_profit_atr_multiple: Decimal = Decimal("1.80"),
        max_holding_bars: int = 12,
        max_entries_per_session: int = 2,
        min_bars_between_entries: int = 120,
        post_exit_cooldown_bars: int = 60,
        max_flips_per_session: int = 1,
        signal_confirm_bars: int = 2,
        min_atr_bps: Decimal = Decimal("3"),
        min_vwap_distance_bps: Decimal = Decimal("2"),
        allow_short: bool = True,
        history_buffer_bars: int = 5,
    ) -> None:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        for name, value in {
            "fast_bars": fast_bars,
            "slow_bars": slow_bars,
            "vwap_lookback_bars": vwap_lookback_bars,
            "volume_lookback_bars": volume_lookback_bars,
            "atr_lookback_bars": atr_lookback_bars,
            "max_holding_bars": max_holding_bars,
            "max_entries_per_session": max_entries_per_session,
            "min_bars_between_entries": min_bars_between_entries,
            "post_exit_cooldown_bars": post_exit_cooldown_bars,
            "signal_confirm_bars": signal_confirm_bars,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if max_flips_per_session < 0:
            raise ValueError("max_flips_per_session must be non-negative")
        if slow_bars < fast_bars:
            raise ValueError("slow_bars must be greater than or equal to fast_bars")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")
        self._symbol = normalized_symbol
        self._timeframe = str(timeframe)
        self._fast_bars = fast_bars
        self._slow_bars = slow_bars
        self._vwap_lookback_bars = vwap_lookback_bars
        self._volume_lookback_bars = volume_lookback_bars
        self._atr_lookback_bars = atr_lookback_bars
        self._entry_return_threshold = _decimal(entry_return_threshold)
        self._min_volume_ratio = _decimal(min_volume_ratio)
        self._max_vwap_distance_bps = _decimal(max_vwap_distance_bps)
        self._target_quantity = _decimal(target_quantity)
        self._stop_atr_multiple = _decimal(stop_atr_multiple)
        self._take_profit_atr_multiple = _decimal(take_profit_atr_multiple)
        self._max_holding_bars = max_holding_bars
        self._max_entries_per_session = max_entries_per_session
        self._min_bars_between_entries = min_bars_between_entries
        self._post_exit_cooldown_bars = post_exit_cooldown_bars
        self._max_flips_per_session = max_flips_per_session
        self._signal_confirm_bars = signal_confirm_bars
        self._min_atr_bps = _decimal(min_atr_bps)
        self._min_vwap_distance_bps = _decimal(min_vwap_distance_bps)
        self._allow_short = allow_short
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "entry_return_threshold": self._entry_return_threshold,
            "min_volume_ratio": self._min_volume_ratio,
            "max_vwap_distance_bps": self._max_vwap_distance_bps,
            "target_quantity": self._target_quantity,
            "stop_atr_multiple": self._stop_atr_multiple,
            "take_profit_atr_multiple": self._take_profit_atr_multiple,
            "min_atr_bps": self._min_atr_bps,
            "min_vwap_distance_bps": self._min_vwap_distance_bps,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._min_vwap_distance_bps > self._max_vwap_distance_bps:
            raise ValueError("min_vwap_distance_bps must be <= max_vwap_distance_bps")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")
        self._asset: AssetRef | None = None
        self._current_side = 0
        self._entry_price: Decimal | None = None
        self._bars_held = 0
        self._last_decision_time: object | None = None
        self._session_id: str | None = None
        self._session_bar_index = 0
        self._session_entries = 0
        self._session_flips = 0
        self._last_entry_bar_index: int | None = None
        self._last_exit_bar_index: int | None = None

    @property
    def _required_history(self) -> int:
        return max(
            self._slow_bars + self._signal_confirm_bars,
            self._vwap_lookback_bars,
            self._volume_lookback_bars + 1,
            self._atr_lookback_bars + 1,
        )

    def initialize(self, ctx: StrategyContext) -> None:
        self._asset = _asset_for_symbol(ctx, self._symbol)
        ctx.subscribe(
            self._asset,
            timeframe=self._timeframe,
            warmup=self._required_history + self._history_buffer_bars,
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._asset is None or ctx.data is None:
            return
        if bar.instrument_id != self._asset.instrument_id:
            return
        history = ctx.data.history(
            self._asset,
            bars=self._required_history,
            timeframe=self._timeframe,
        )
        if len(history) < self._required_history:
            return
        latest = history[-1]
        if latest.end_time == self._last_decision_time:
            return
        self._last_decision_time = latest.end_time
        self._roll_session_if_needed(str(latest.session_id))
        self._session_bar_index += 1

        atr = _atr(history, self._atr_lookback_bars)
        if self._current_side != 0 and self._exit_open_position(ctx, latest, atr):
            return

        signal_side = self._entry_side(history, atr)
        if signal_side == 0 or signal_side == self._current_side:
            return
        if self._current_side != 0:
            self._close(ctx, reason="microtrend_flip")
            return
        if self._entry_frequency_blocked():
            return
        self._enter(ctx, signal_side, latest.close)

    def _entry_side(self, history: tuple[Bar, ...], atr: Decimal) -> int:
        latest = history[-1]
        if latest.close <= Decimal("0"):
            return 0
        atr_bps = atr / latest.close * _BPS if atr > Decimal("0") else Decimal("0")
        if atr_bps < self._min_atr_bps:
            return 0
        if history[-1 - self._fast_bars].close <= Decimal("0"):
            return 0
        if history[-1 - self._slow_bars].close <= Decimal("0"):
            return 0
        fast_return = latest.close / history[-1 - self._fast_bars].close - Decimal("1")
        slow_return = latest.close / history[-1 - self._slow_bars].close - Decimal("1")
        if abs(fast_return) < self._entry_return_threshold:
            return 0
        if fast_return > Decimal("0") and slow_return <= Decimal("0"):
            return 0
        if fast_return < Decimal("0") and slow_return >= Decimal("0"):
            return 0
        side = 1 if fast_return > Decimal("0") else -1
        if side < 0 and not self._allow_short:
            return 0
        if not self._signal_confirmed(history, side):
            return 0
        volume_ratio = _volume_ratio(history, self._volume_lookback_bars)
        if volume_ratio < self._min_volume_ratio:
            return 0
        vwap = _rolling_vwap(history[-self._vwap_lookback_bars :])
        if vwap <= Decimal("0"):
            return 0
        distance_bps = abs(latest.close / vwap - Decimal("1")) * _BPS
        if distance_bps < self._min_vwap_distance_bps:
            return 0
        if distance_bps > self._max_vwap_distance_bps:
            return 0
        if fast_return > Decimal("0") and latest.close > vwap:
            return 1
        if fast_return < Decimal("0") and latest.close < vwap and self._allow_short:
            return -1
        return 0

    def _signal_confirmed(self, history: tuple[Bar, ...], side: int) -> bool:
        for offset in range(self._signal_confirm_bars):
            latest = history[-1 - offset]
            fast_anchor = history[-1 - offset - self._fast_bars]
            slow_anchor = history[-1 - offset - self._slow_bars]
            if fast_anchor.close <= Decimal("0") or slow_anchor.close <= Decimal("0"):
                return False
            fast_return = latest.close / fast_anchor.close - Decimal("1")
            slow_return = latest.close / slow_anchor.close - Decimal("1")
            if side > 0 and (fast_return <= Decimal("0") or slow_return <= Decimal("0")):
                return False
            if side < 0 and (fast_return >= Decimal("0") or slow_return >= Decimal("0")):
                return False
        return True

    def _roll_session_if_needed(self, session_id: str) -> None:
        if self._session_id == session_id:
            return
        self._session_id = session_id
        self._session_bar_index = 0
        self._session_entries = 0
        self._session_flips = 0
        self._last_entry_bar_index = None
        self._last_exit_bar_index = None

    def _entry_frequency_blocked(self) -> bool:
        if self._session_entries >= self._max_entries_per_session:
            return True
        if self._session_flips > self._max_flips_per_session:
            return True
        if (
            self._last_entry_bar_index is not None
            and self._session_bar_index - self._last_entry_bar_index
            < self._min_bars_between_entries
        ):
            return True
        return (
            self._last_exit_bar_index is not None
            and self._session_bar_index - self._last_exit_bar_index < self._post_exit_cooldown_bars
        )

    def _exit_open_position(self, ctx: StrategyContext, bar: Bar, atr: Decimal) -> bool:
        if self._asset is None or self._entry_price is None:
            return False
        self._bars_held += 1
        if self._bars_held >= self._max_holding_bars:
            self._close(ctx, reason="max_holding_bars")
            return True
        if atr <= Decimal("0"):
            return False
        if self._current_side > 0:
            move = bar.close - self._entry_price
        else:
            move = self._entry_price - bar.close
        if move <= -self._stop_atr_multiple * atr:
            self._close(ctx, reason="atr_stop")
            return True
        if move >= self._take_profit_atr_multiple * atr:
            self._close(ctx, reason="atr_take_profit")
            return True
        return False

    def _enter(self, ctx: StrategyContext, side: int, entry_price: Decimal) -> None:
        if self._asset is None:
            return
        quantity = self._target_quantity * Decimal(side)
        ctx.target_quantity(
            self._asset,
            quantity,
            metadata={"entry_reason": "microtrend_scalp", "model": "precious-metal-hft-v1"},
        )
        self._current_side = side
        self._entry_price = entry_price
        self._bars_held = 0
        self._session_entries += 1
        self._last_entry_bar_index = self._session_bar_index

    def _close(self, ctx: StrategyContext, *, reason: str) -> None:
        if self._asset is None or self._current_side == 0:
            return
        ctx.close(
            self._asset,
            metadata={"exit_reason": reason, "model": "precious-metal-hft-v1"},
        )
        self._current_side = 0
        self._entry_price = None
        self._bars_held = 0
        self._last_exit_bar_index = self._session_bar_index
        if reason == "microtrend_flip":
            self._session_flips += 1


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return Decimal("0")
    return sum(items, Decimal("0")) / Decimal(len(items))


def _volume_ratio(history: tuple[Bar, ...], lookback: int) -> Decimal:
    if len(history) < lookback + 1:
        return Decimal("0")
    baseline = _average(bar.volume for bar in history[-lookback - 1 : -1])
    if baseline <= Decimal("0"):
        return Decimal("1")
    return history[-1].volume / baseline


def _rolling_vwap(history: tuple[Bar, ...]) -> Decimal:
    total_volume = sum((bar.volume for bar in history), Decimal("0"))
    if total_volume <= Decimal("0"):
        return _average(bar.close for bar in history)
    notional = Decimal("0")
    for bar in history:
        price = (
            bar.vwap if bar.vwap is not None else (bar.high + bar.low + bar.close) / Decimal("3")
        )
        notional += price * bar.volume
    return notional / total_volume


def _atr(history: tuple[Bar, ...], lookback: int) -> Decimal:
    if len(history) < lookback + 1:
        return Decimal("0")
    ranges: list[Decimal] = []
    window = history[-lookback - 1 :]
    for previous, current in itertools.pairwise(window):
        high_low = current.high - current.low
        high_close = abs(current.high - previous.close)
        low_close = abs(current.low - previous.close)
        ranges.append(max(high_low, high_close, low_close))
    return _average(ranges)


__all__ = ["PreciousMetalMicrotrendScalperStrategy"]
