"""Research-only precious-metal dual-signal confirmation strategy."""

from __future__ import annotations

import itertools
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


class PreciousMetalDualSignalStrategy(Strategy):
    """Trade GC/SI only when two completed-bar research signals agree."""

    def __init__(
        self,
        *,
        trade_symbol: str = "GC",
        primary_symbol: str = "REALYIELD10Y",
        secondary_symbol: str = "COT_GC",
        timeframe: str = "1d",
        primary_lookback_bars: int = 60,
        secondary_lookback_bars: int = 26,
        primary_signal_mode: str = "change",
        secondary_signal_mode: str = "change",
        primary_direction: str = "fade",
        secondary_direction: str = "follow",
        primary_entry_z: Decimal = Decimal("0.75"),
        secondary_entry_z: Decimal = Decimal("0.75"),
        target_quantity: Decimal = Decimal("1"),
        min_signal_std: Decimal = Decimal("0.0001"),
        trend_lookback_bars: int = 0,
        min_trend_return: Decimal = Decimal("0"),
        allow_short: bool = False,
        history_buffer_bars: int = 2,
    ) -> None:
        self._trade_symbol = _symbol(trade_symbol, "trade_symbol")
        self._primary_symbol = _symbol(primary_symbol, "primary_symbol")
        self._secondary_symbol = _symbol(secondary_symbol, "secondary_symbol")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        for name, value in {
            "primary_lookback_bars": primary_lookback_bars,
            "secondary_lookback_bars": secondary_lookback_bars,
        }.items():
            if value < 3:
                raise ValueError(f"{name} must be at least 3")
        self._primary_signal_mode = _mode(primary_signal_mode, "primary_signal_mode")
        self._secondary_signal_mode = _mode(secondary_signal_mode, "secondary_signal_mode")
        self._primary_direction = _direction(primary_direction, "primary_direction")
        self._secondary_direction = _direction(secondary_direction, "secondary_direction")
        if trend_lookback_bars < 0:
            raise ValueError("trend_lookback_bars must be non-negative")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")

        self._timeframe = str(timeframe)
        self._primary_lookback_bars = primary_lookback_bars
        self._secondary_lookback_bars = secondary_lookback_bars
        self._primary_entry_z = _decimal(primary_entry_z)
        self._secondary_entry_z = _decimal(secondary_entry_z)
        self._target_quantity = _decimal(target_quantity)
        self._min_signal_std = _decimal(min_signal_std)
        self._trend_lookback_bars = trend_lookback_bars
        self._min_trend_return = _decimal(min_trend_return)
        self._allow_short = allow_short
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "primary_entry_z": self._primary_entry_z,
            "secondary_entry_z": self._secondary_entry_z,
            "target_quantity": self._target_quantity,
            "min_signal_std": self._min_signal_std,
            "min_trend_return": self._min_trend_return,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._primary_entry_z == Decimal("0"):
            raise ValueError("primary_entry_z must be positive")
        if self._secondary_entry_z == Decimal("0"):
            raise ValueError("secondary_entry_z must be positive")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")
        if self._min_signal_std == Decimal("0"):
            raise ValueError("min_signal_std must be positive")

        self._trade_asset: AssetRef | None = None
        self._primary_asset: AssetRef | None = None
        self._secondary_asset: AssetRef | None = None
        self._current_side = 0
        self._last_decision_time: object | None = None

    def initialize(self, ctx: StrategyContext) -> None:
        self._trade_asset = _asset_for_symbol(ctx, self._trade_symbol)
        self._primary_asset = _asset_for_symbol(ctx, self._primary_symbol)
        self._secondary_asset = _asset_for_symbol(ctx, self._secondary_symbol)
        ctx.subscribe(
            self._trade_asset,
            timeframe=self._timeframe,
            warmup=max(1, self._trend_lookback_bars + 1) + self._history_buffer_bars,
        )
        ctx.subscribe(
            self._primary_asset,
            timeframe=self._timeframe,
            warmup=self._required_history(
                self._primary_signal_mode,
                self._primary_lookback_bars,
            )
            + self._history_buffer_bars,
        )
        ctx.subscribe(
            self._secondary_asset,
            timeframe=self._timeframe,
            warmup=self._required_history(
                self._secondary_signal_mode,
                self._secondary_lookback_bars,
            )
            + self._history_buffer_bars,
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if (
            self._trade_asset is None
            or self._primary_asset is None
            or self._secondary_asset is None
            or ctx.data is None
        ):
            return
        if bar.instrument_id != self._trade_asset.instrument_id:
            return
        if bar.end_time == self._last_decision_time:
            return
        self._last_decision_time = bar.end_time

        primary_side = self._signal_side(
            ctx,
            self._primary_asset,
            lookback=self._primary_lookback_bars,
            signal_mode=self._primary_signal_mode,
            direction=self._primary_direction,
            entry_z=self._primary_entry_z,
        )
        secondary_side = self._signal_side(
            ctx,
            self._secondary_asset,
            lookback=self._secondary_lookback_bars,
            signal_mode=self._secondary_signal_mode,
            direction=self._secondary_direction,
            entry_z=self._secondary_entry_z,
        )
        next_side = primary_side if primary_side != 0 and primary_side == secondary_side else 0
        if next_side < 0 and not self._allow_short:
            next_side = 0
        next_side = self._apply_trend_filter(ctx, next_side)
        if next_side == self._current_side:
            return
        if next_side == 0:
            ctx.close(self._trade_asset)
        else:
            ctx.target_quantity(self._trade_asset, Decimal(next_side) * self._target_quantity)
        self._current_side = next_side

    def _signal_side(
        self,
        ctx: StrategyContext,
        asset: AssetRef,
        *,
        lookback: int,
        signal_mode: str,
        direction: str,
        entry_z: Decimal,
    ) -> int:
        required = self._required_history(signal_mode, lookback)
        history = ctx.data.history(asset, bars=required, timeframe=self._timeframe)
        if len(history) < required:
            return 0
        values = self._signal_values(history, lookback=lookback, signal_mode=signal_mode)
        z_score = self._z_score(values)
        if z_score is None:
            return 0
        if direction == "follow":
            if z_score >= entry_z:
                return 1
            if z_score <= -entry_z:
                return -1
            return 0
        if z_score >= entry_z:
            return -1
        if z_score <= -entry_z:
            return 1
        return 0

    @staticmethod
    def _required_history(signal_mode: str, lookback: int) -> int:
        if signal_mode == "change":
            return lookback + 1
        return lookback

    @staticmethod
    def _signal_values(
        history: tuple[Bar, ...],
        *,
        lookback: int,
        signal_mode: str,
    ) -> tuple[Decimal, ...]:
        values = tuple(item.close for item in history)
        if signal_mode == "level":
            return values[-lookback:]
        return tuple(current - previous for previous, current in itertools.pairwise(values))

    def _z_score(self, values: tuple[Decimal, ...]) -> Decimal | None:
        mean = sum(values, Decimal("0")) / Decimal(len(values))
        variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
        std = variance.sqrt()
        if std < self._min_signal_std:
            return None
        return (values[-1] - mean) / std

    def _apply_trend_filter(self, ctx: StrategyContext, side: int) -> int:
        if side == 0 or self._trend_lookback_bars == 0:
            return side
        if self._trade_asset is None:
            raise RuntimeError("strategy must be initialized before trend filtering")
        history = ctx.data.history(
            self._trade_asset,
            bars=self._trend_lookback_bars + 1,
            timeframe=self._timeframe,
        )
        if len(history) < self._trend_lookback_bars + 1:
            return 0
        start = history[0].close
        end = history[-1].close
        if start <= Decimal("0"):
            return 0
        trend_return = (end - start) / start
        if side > 0 and trend_return < self._min_trend_return:
            return 0
        if side < 0 and trend_return > -self._min_trend_return:
            return 0
        return side


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


def _symbol(value: str, name: str) -> str:
    normalized = str(value).strip().upper()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _mode(value: str, name: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in {"level", "change"}:
        raise ValueError(f"{name} must be 'level' or 'change'")
    return normalized


def _direction(value: str, name: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in {"follow", "fade"}:
        raise ValueError(f"{name} must be 'follow' or 'fade'")
    return normalized


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value))


__all__ = ["PreciousMetalDualSignalStrategy"]
