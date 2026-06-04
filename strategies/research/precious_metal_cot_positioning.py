"""Research-only precious-metal COT positioning strategy."""

from __future__ import annotations

import itertools
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


class PreciousMetalCotPositioningStrategy(Strategy):
    """Trade GC/SI from completed CFTC managed-money positioning signals."""

    def __init__(
        self,
        *,
        trade_symbol: str = "GC",
        cot_symbol: str = "COT_GC",
        timeframe: str = "1d",
        cot_lookback_bars: int = 52,
        signal_mode: str = "level",
        positioning_direction: str = "fade",
        entry_z: Decimal = Decimal("1.25"),
        exit_z: Decimal = Decimal("0.25"),
        target_quantity: Decimal = Decimal("1"),
        min_signal_std: Decimal = Decimal("0.0001"),
        trend_lookback_bars: int = 0,
        min_trend_return: Decimal = Decimal("0"),
        allow_short: bool = True,
        history_buffer_bars: int = 2,
    ) -> None:
        normalized_trade_symbol = str(trade_symbol).strip().upper()
        normalized_cot_symbol = str(cot_symbol).strip().upper()
        normalized_signal_mode = str(signal_mode).strip().lower()
        normalized_direction = str(positioning_direction).strip().lower()
        if not normalized_trade_symbol:
            raise ValueError("trade_symbol must not be empty")
        if not normalized_cot_symbol:
            raise ValueError("cot_symbol must not be empty")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        if cot_lookback_bars < 3:
            raise ValueError("cot_lookback_bars must be at least 3")
        if normalized_signal_mode not in {"level", "change"}:
            raise ValueError("signal_mode must be 'level' or 'change'")
        if normalized_direction not in {"follow", "fade"}:
            raise ValueError("positioning_direction must be 'follow' or 'fade'")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")
        if trend_lookback_bars < 0:
            raise ValueError("trend_lookback_bars must be non-negative")

        self._trade_symbol = normalized_trade_symbol
        self._cot_symbol = normalized_cot_symbol
        self._timeframe = str(timeframe)
        self._cot_lookback_bars = cot_lookback_bars
        self._signal_mode = normalized_signal_mode
        self._positioning_direction = normalized_direction
        self._entry_z = _decimal(entry_z)
        self._exit_z = _decimal(exit_z)
        self._target_quantity = _decimal(target_quantity)
        self._min_signal_std = _decimal(min_signal_std)
        self._trend_lookback_bars = trend_lookback_bars
        self._min_trend_return = _decimal(min_trend_return)
        self._allow_short = allow_short
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "entry_z": self._entry_z,
            "exit_z": self._exit_z,
            "target_quantity": self._target_quantity,
            "min_signal_std": self._min_signal_std,
            "min_trend_return": self._min_trend_return,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._entry_z == Decimal("0"):
            raise ValueError("entry_z must be positive")
        if self._exit_z >= self._entry_z:
            raise ValueError("exit_z must be less than entry_z")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")
        if self._min_signal_std == Decimal("0"):
            raise ValueError("min_signal_std must be positive")

        self._trade_asset: AssetRef | None = None
        self._cot_asset: AssetRef | None = None
        self._current_side = 0
        self._last_decision_time: object | None = None

    @property
    def _required_cot_history(self) -> int:
        if self._signal_mode == "change":
            return self._cot_lookback_bars + 1
        return self._cot_lookback_bars

    def initialize(self, ctx: StrategyContext) -> None:
        self._trade_asset = _asset_for_symbol(ctx, self._trade_symbol)
        self._cot_asset = _asset_for_symbol(ctx, self._cot_symbol)
        ctx.subscribe(
            self._trade_asset,
            timeframe=self._timeframe,
            warmup=max(1, self._trend_lookback_bars + 1) + self._history_buffer_bars,
        )
        ctx.subscribe(
            self._cot_asset,
            timeframe=self._timeframe,
            warmup=self._required_cot_history + self._history_buffer_bars,
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._trade_asset is None or self._cot_asset is None or ctx.data is None:
            return
        if bar.instrument_id != self._trade_asset.instrument_id:
            return
        if bar.end_time == self._last_decision_time:
            return
        self._last_decision_time = bar.end_time

        cot_history = ctx.data.history(
            self._cot_asset,
            bars=self._required_cot_history,
            timeframe=self._timeframe,
        )
        if len(cot_history) < self._required_cot_history:
            return
        signal_values = self._signal_values(cot_history)
        z_score = self._z_score(signal_values)
        if z_score is None:
            return
        next_side = self._next_side(z_score)
        next_side = self._apply_trend_filter(ctx, next_side)
        if next_side == self._current_side:
            return
        if next_side == 0:
            ctx.close(self._trade_asset)
        else:
            ctx.target_quantity(self._trade_asset, Decimal(next_side) * self._target_quantity)
        self._current_side = next_side

    def _signal_values(self, cot_history: tuple[Bar, ...]) -> tuple[Decimal, ...]:
        values = tuple(item.close for item in cot_history)
        if self._signal_mode == "level":
            return values[-self._cot_lookback_bars :]
        return tuple(current - previous for previous, current in itertools.pairwise(values))

    def _z_score(self, values: tuple[Decimal, ...]) -> Decimal | None:
        if len(values) < self._cot_lookback_bars:
            return None
        mean = sum(values, Decimal("0")) / Decimal(len(values))
        variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
        std = variance.sqrt()
        if std < self._min_signal_std:
            return None
        return (values[-1] - mean) / std

    def _next_side(self, z_score: Decimal) -> int:
        entry_side = self._entry_side(z_score)
        if entry_side != 0:
            if entry_side < 0 and not self._allow_short:
                return 0
            return entry_side
        if self._current_side == 0:
            return 0
        if self._should_exit(z_score):
            return 0
        return self._current_side

    def _entry_side(self, z_score: Decimal) -> int:
        if self._positioning_direction == "follow":
            if z_score >= self._entry_z:
                return 1
            if z_score <= -self._entry_z:
                return -1
            return 0
        if z_score >= self._entry_z:
            return -1
        if z_score <= -self._entry_z:
            return 1
        return 0

    def _should_exit(self, z_score: Decimal) -> bool:
        if self._current_side > 0:
            if self._positioning_direction == "follow":
                return z_score <= self._exit_z
            return z_score >= -self._exit_z
        if self._current_side < 0:
            if self._positioning_direction == "follow":
                return z_score >= -self._exit_z
            return z_score <= self._exit_z
        return False

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


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value))


__all__ = ["PreciousMetalCotPositioningStrategy"]
