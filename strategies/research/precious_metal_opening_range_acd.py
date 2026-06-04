"""Opening-range ACD/breakout/failure strategy for precious-metal futures."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


@dataclass(slots=True)
class _SessionState:
    session_id: str | None = None
    bar_count: int = 0
    opening_high: Decimal | None = None
    opening_low: Decimal | None = None
    opening_complete: bool = False
    pierced_high: bool = False
    pierced_low: bool = False
    entries: int = 0
    bars_held: int = 0

    @property
    def width(self) -> Decimal | None:
        if self.opening_high is None or self.opening_low is None:
            return None
        return self.opening_high - self.opening_low


class PreciousMetalOpeningRangeAcdStrategy(Strategy):
    """Completed-bar opening-range scalper.

    `mode="breakout"` trades A-up/A-down continuation.
    `mode="failure"` trades false breaks back through the opening range.
    """

    def __init__(
        self,
        *,
        symbol: str = "GC",
        timeframe: str = "1m",
        mode: str = "breakout",
        opening_range_bars: int = 5,
        max_entry_bars: int = 45,
        target_quantity: Decimal = Decimal("1"),
        entry_buffer_ratio: Decimal = Decimal("0.10"),
        stop_range_multiple: Decimal = Decimal("0.75"),
        target_range_multiple: Decimal = Decimal("1.25"),
        max_holding_bars: int = 20,
        max_entries_per_session: int = 1,
        min_range_width: Decimal = Decimal("0"),
        allow_short: bool = True,
    ) -> None:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in {"breakout", "failure"}:
            raise ValueError("mode must be 'breakout' or 'failure'")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        for name, value in {
            "opening_range_bars": opening_range_bars,
            "max_entry_bars": max_entry_bars,
            "max_holding_bars": max_holding_bars,
            "max_entries_per_session": max_entries_per_session,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if max_entry_bars <= opening_range_bars:
            raise ValueError("max_entry_bars must be greater than opening_range_bars")
        self._symbol = normalized_symbol
        self._timeframe = str(timeframe)
        self._mode = normalized_mode
        self._opening_range_bars = opening_range_bars
        self._max_entry_bars = max_entry_bars
        self._target_quantity = _decimal(target_quantity)
        self._entry_buffer_ratio = _decimal(entry_buffer_ratio)
        self._stop_range_multiple = _decimal(stop_range_multiple)
        self._target_range_multiple = _decimal(target_range_multiple)
        self._max_holding_bars = max_holding_bars
        self._max_entries_per_session = max_entries_per_session
        self._min_range_width = _decimal(min_range_width)
        self._allow_short = allow_short
        for name, value in {
            "target_quantity": self._target_quantity,
            "entry_buffer_ratio": self._entry_buffer_ratio,
            "stop_range_multiple": self._stop_range_multiple,
            "target_range_multiple": self._target_range_multiple,
            "min_range_width": self._min_range_width,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")
        if self._stop_range_multiple == Decimal("0"):
            raise ValueError("stop_range_multiple must be positive")
        if self._target_range_multiple == Decimal("0"):
            raise ValueError("target_range_multiple must be positive")
        self._asset: AssetRef | None = None
        self._session = _SessionState()
        self._current_side = 0
        self._entry_price: Decimal | None = None
        self._entry_width: Decimal | None = None
        self._last_decision_time: object | None = None

    def initialize(self, ctx: StrategyContext) -> None:
        self._asset = _asset_for_symbol(ctx, self._symbol)
        ctx.subscribe(self._asset, timeframe=self._timeframe, warmup=self._opening_range_bars)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._asset is None or bar.instrument_id != self._asset.instrument_id:
            return
        if bar.end_time == self._last_decision_time:
            return
        self._last_decision_time = bar.end_time
        self._roll_session_if_needed(ctx, bar.session_id)
        if self._update_opening_range(bar):
            return
        if not self._session.opening_complete:
            return
        if self._current_side != 0:
            self._manage_open_position(ctx, bar)
            return
        if self._entry_blocked():
            return
        self._evaluate_entry(ctx, bar)

    def _roll_session_if_needed(self, ctx: StrategyContext, session_id: str) -> None:
        if self._session.session_id is None:
            self._session = _SessionState(session_id=session_id)
            return
        if self._session.session_id == session_id:
            return
        self._close(ctx, reason="session_roll_flat")
        self._session = _SessionState(session_id=session_id)

    def _update_opening_range(self, bar: Bar) -> bool:
        self._session.bar_count += 1
        if self._session.bar_count > self._opening_range_bars:
            return False
        self._session.opening_high = (
            bar.high
            if self._session.opening_high is None
            else max(self._session.opening_high, bar.high)
        )
        self._session.opening_low = (
            bar.low
            if self._session.opening_low is None
            else min(self._session.opening_low, bar.low)
        )
        if self._session.bar_count >= self._opening_range_bars:
            self._session.opening_complete = True
        return True

    def _entry_blocked(self) -> bool:
        return (
            self._session.bar_count > self._max_entry_bars
            or self._session.entries >= self._max_entries_per_session
        )

    def _evaluate_entry(self, ctx: StrategyContext, bar: Bar) -> None:
        width = self._session.width
        if width is None or width <= self._min_range_width:
            return
        if self._session.opening_high is None or self._session.opening_low is None:
            return
        buffer = width * self._entry_buffer_ratio
        high_trigger = self._session.opening_high + buffer
        low_trigger = self._session.opening_low - buffer
        if self._mode == "breakout":
            if bar.close > high_trigger:
                self._enter(ctx, 1, bar, width, reason="acd_breakout_long")
            elif bar.close < low_trigger and self._allow_short:
                self._enter(ctx, -1, bar, width, reason="acd_breakout_short")
            return
        if bar.high > high_trigger:
            self._session.pierced_high = True
        if bar.low < low_trigger:
            self._session.pierced_low = True
        if (
            self._session.pierced_high
            and bar.close < self._session.opening_high
            and self._allow_short
        ):
            self._enter(ctx, -1, bar, width, reason="acd_failure_short")
        elif self._session.pierced_low and bar.close > self._session.opening_low:
            self._enter(ctx, 1, bar, width, reason="acd_failure_long")

    def _manage_open_position(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._entry_price is None or self._entry_width is None:
            return
        self._session.bars_held += 1
        if self._session.bars_held >= self._max_holding_bars:
            self._close(ctx, reason="max_holding_bars")
            return
        direction = Decimal(self._current_side)
        favorable_move = direction * (bar.close - self._entry_price)
        if favorable_move <= -self._entry_width * self._stop_range_multiple:
            self._close(ctx, reason="range_stop")
        elif favorable_move >= self._entry_width * self._target_range_multiple:
            self._close(ctx, reason="range_target")

    def _enter(
        self,
        ctx: StrategyContext,
        side: int,
        bar: Bar,
        width: Decimal,
        *,
        reason: str,
    ) -> None:
        if self._asset is None:
            return
        ctx.target_quantity(
            self._asset,
            self._target_quantity * Decimal(side),
            metadata={
                "entry_reason": reason,
                "session_id": str(bar.session_id),
                "model": "precious-metal-hft-v1",
            },
        )
        self._current_side = side
        self._entry_price = bar.close
        self._entry_width = width
        self._session.entries += 1
        self._session.bars_held = 0

    def _close(self, ctx: StrategyContext, *, reason: str) -> None:
        if self._asset is None or self._current_side == 0:
            return
        ctx.close(
            self._asset,
            metadata={
                "exit_reason": reason,
                "session_id": str(self._session.session_id),
                "model": "precious-metal-hft-v1",
            },
        )
        self._current_side = 0
        self._entry_price = None
        self._entry_width = None
        self._session.bars_held = 0


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


__all__ = ["PreciousMetalOpeningRangeAcdStrategy"]
