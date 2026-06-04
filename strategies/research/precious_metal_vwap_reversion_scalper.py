"""Precious-metal VWAP mean-reversion scalper using the public QTS SDK."""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext

_BPS = Decimal("10000")


class PreciousMetalVwapReversionScalperStrategy(Strategy):
    """Short-horizon VWAP deviation reversion strategy.

    This is designed for liquid products such as GC/SI/MGC/MES-like metal
    contracts where short intraday dislocations around volume-weighted fair
    value can revert quickly. It uses completed bars only and closes positions
    through Strategy SDK target intents.
    """

    def __init__(
        self,
        *,
        symbol: str = "GC",
        timeframe: str = "1m",
        lookback_bars: int = 60,
        trend_lookback_bars: int = 20,
        volume_lookback_bars: int = 20,
        atr_lookback_bars: int = 14,
        entry_z: Decimal = Decimal("2.00"),
        exit_z: Decimal = Decimal("0.35"),
        stop_z: Decimal = Decimal("3.50"),
        max_trend_bps: Decimal = Decimal("35"),
        min_volume_ratio: Decimal = Decimal("0.80"),
        target_quantity: Decimal = Decimal("1"),
        stop_atr_multiple: Decimal = Decimal("1.50"),
        max_holding_bars: int = 15,
        max_entries_per_session: int = 2,
        min_bars_between_entries: int = 120,
        post_exit_cooldown_bars: int = 60,
        rearm_z: Decimal = Decimal("0.75"),
        allow_short: bool = True,
        history_buffer_bars: int = 5,
    ) -> None:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        for name, value in {
            "lookback_bars": lookback_bars,
            "trend_lookback_bars": trend_lookback_bars,
            "volume_lookback_bars": volume_lookback_bars,
            "atr_lookback_bars": atr_lookback_bars,
            "max_holding_bars": max_holding_bars,
            "max_entries_per_session": max_entries_per_session,
            "min_bars_between_entries": min_bars_between_entries,
            "post_exit_cooldown_bars": post_exit_cooldown_bars,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")
        self._symbol = normalized_symbol
        self._timeframe = str(timeframe)
        self._lookback_bars = lookback_bars
        self._trend_lookback_bars = trend_lookback_bars
        self._volume_lookback_bars = volume_lookback_bars
        self._atr_lookback_bars = atr_lookback_bars
        self._entry_z = _decimal(entry_z)
        self._exit_z = _decimal(exit_z)
        self._stop_z = _decimal(stop_z)
        self._max_trend_bps = _decimal(max_trend_bps)
        self._min_volume_ratio = _decimal(min_volume_ratio)
        self._target_quantity = _decimal(target_quantity)
        self._stop_atr_multiple = _decimal(stop_atr_multiple)
        self._max_holding_bars = max_holding_bars
        self._max_entries_per_session = max_entries_per_session
        self._min_bars_between_entries = min_bars_between_entries
        self._post_exit_cooldown_bars = post_exit_cooldown_bars
        self._rearm_z = _decimal(rearm_z)
        self._allow_short = allow_short
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "entry_z": self._entry_z,
            "exit_z": self._exit_z,
            "stop_z": self._stop_z,
            "max_trend_bps": self._max_trend_bps,
            "min_volume_ratio": self._min_volume_ratio,
            "target_quantity": self._target_quantity,
            "stop_atr_multiple": self._stop_atr_multiple,
            "rearm_z": self._rearm_z,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._exit_z >= self._entry_z:
            raise ValueError("exit_z must be less than entry_z")
        if self._rearm_z >= self._entry_z:
            raise ValueError("rearm_z must be less than entry_z")
        if self._stop_z <= self._entry_z:
            raise ValueError("stop_z must be greater than entry_z")
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
        self._last_entry_bar_index: int | None = None
        self._last_exit_bar_index: int | None = None
        self._z_rearmed = True

    @property
    def _required_history(self) -> int:
        return max(
            self._lookback_bars,
            self._trend_lookback_bars + 1,
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

        z_score = _vwap_deviation_z(history[-self._lookback_bars :])
        if abs(z_score) <= self._rearm_z:
            self._z_rearmed = True
        atr = _atr(history, self._atr_lookback_bars)
        if self._current_side != 0 and self._exit_open_position(ctx, latest, z_score, atr):
            return

        signal_side = self._entry_side(history, z_score)
        if signal_side == 0 or signal_side == self._current_side:
            return
        if self._current_side != 0:
            self._close(ctx, reason="vwap_reversion_flip")
            return
        if self._entry_frequency_blocked():
            return
        self._enter(ctx, signal_side, latest.close)

    def _entry_side(self, history: tuple[Bar, ...], z_score: Decimal) -> int:
        if not self._z_rearmed:
            return 0
        latest = history[-1]
        previous = history[-1 - self._trend_lookback_bars]
        if previous.close <= Decimal("0"):
            return 0
        trend_bps = abs(latest.close / previous.close - Decimal("1")) * _BPS
        if trend_bps > self._max_trend_bps:
            return 0
        if _volume_ratio(history, self._volume_lookback_bars) < self._min_volume_ratio:
            return 0
        if z_score <= -self._entry_z:
            return 1
        if z_score >= self._entry_z and self._allow_short:
            return -1
        return 0

    def _roll_session_if_needed(self, session_id: str) -> None:
        if self._session_id == session_id:
            return
        self._session_id = session_id
        self._session_bar_index = 0
        self._session_entries = 0
        self._last_entry_bar_index = None
        self._last_exit_bar_index = None
        self._z_rearmed = True

    def _entry_frequency_blocked(self) -> bool:
        if self._session_entries >= self._max_entries_per_session:
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

    def _exit_open_position(
        self,
        ctx: StrategyContext,
        bar: Bar,
        z_score: Decimal,
        atr: Decimal,
    ) -> bool:
        if self._asset is None or self._entry_price is None:
            return False
        self._bars_held += 1
        if abs(z_score) <= self._exit_z:
            self._close(ctx, reason="vwap_reverted")
            return True
        if abs(z_score) >= self._stop_z:
            self._close(ctx, reason="vwap_deviation_stop")
            return True
        if self._bars_held >= self._max_holding_bars:
            self._close(ctx, reason="max_holding_bars")
            return True
        if atr > Decimal("0"):
            move_against = (
                self._entry_price - bar.close
                if self._current_side > 0
                else bar.close - self._entry_price
            )
            if move_against >= self._stop_atr_multiple * atr:
                self._close(ctx, reason="atr_stop")
                return True
        return False

    def _enter(self, ctx: StrategyContext, side: int, entry_price: Decimal) -> None:
        if self._asset is None:
            return
        ctx.target_quantity(
            self._asset,
            self._target_quantity * Decimal(side),
            metadata={"entry_reason": "vwap_reversion_scalp", "model": "precious-metal-hft-v1"},
        )
        self._current_side = side
        self._entry_price = entry_price
        self._bars_held = 0
        self._session_entries += 1
        self._last_entry_bar_index = self._session_bar_index
        self._z_rearmed = False

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


def _stddev(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if len(items) < 2:
        return Decimal("0")
    mean = _average(items)
    variance = sum((item - mean) ** 2 for item in items) / Decimal(len(items))
    return variance.sqrt() if variance > Decimal("0") else Decimal("0")


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


def _vwap_deviation_z(history: tuple[Bar, ...]) -> Decimal:
    vwap = _rolling_vwap(history)
    if vwap <= Decimal("0"):
        return Decimal("0")
    deviations = tuple(bar.close / vwap - Decimal("1") for bar in history)
    std = _stddev(deviations)
    if std <= Decimal("0"):
        return Decimal("0")
    return (deviations[-1] - _average(deviations)) / std


def _volume_ratio(history: tuple[Bar, ...], lookback: int) -> Decimal:
    if len(history) < lookback + 1:
        return Decimal("0")
    baseline = _average(bar.volume for bar in history[-lookback - 1 : -1])
    if baseline <= Decimal("0"):
        return Decimal("1")
    return history[-1].volume / baseline


def _atr(history: tuple[Bar, ...], lookback: int) -> Decimal:
    if len(history) < lookback + 1:
        return Decimal("0")
    ranges: list[Decimal] = []
    window = history[-lookback - 1 :]
    for previous, current in itertools.pairwise(window):
        ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    return _average(ranges)


__all__ = ["PreciousMetalVwapReversionScalperStrategy"]
