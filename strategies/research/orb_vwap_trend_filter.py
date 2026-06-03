"""Research-only opening-range breakout with VWAP and trend entry filters."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetIndicator, AssetRef, Strategy, StrategyContext


class _Mode(StrEnum):
    BREAKOUT = "breakout"
    FAILURE = "failure"


class _TrendFilter(StrEnum):
    OFF = "off"
    ROC = "roc"


@dataclass(slots=True)
class _SessionState:
    session_id: str | None = None
    opening_high: Decimal | None = None
    opening_low: Decimal | None = None
    opening_complete: bool = False
    pierced_high: bool = False
    pierced_low: bool = False
    entries: int = 0
    bars_held: int = 0
    vwap_history: deque[Decimal] = field(default_factory=deque)

    @property
    def opening_width(self) -> Decimal | None:
        if self.opening_high is None or self.opening_low is None:
            return None
        return self.opening_high - self.opening_low


@dataclass(frozen=True, slots=True)
class _Indicators:
    vwap: AssetIndicator
    trend: AssetIndicator
    atr: AssetIndicator


class OrbVwapTrendFilterStrategy(Strategy):
    """Opening-range breakout/failure with completed-bar VWAP and ROC filters.

    The opening range remains the only entry trigger. VWAP and trend signals are
    entry filters only; they never emit independent orders. All inputs come from
    completed strategy-facing bars and SDK indicators.
    """

    def __init__(
        self,
        *,
        symbol: str = "GC",
        timeframe: str = "1m",
        mode: str = "breakout",
        range_start_et: str = "18:00",
        session_close_et: str = "17:00",
        opening_range_minutes: int = 60,
        max_entry_elapsed_minutes: int = 22 * 60,
        minutes_before_close_flat: int = 60,
        target_quantity: Decimal = Decimal("1"),
        breakout_buffer_ratio: Decimal = Decimal("0"),
        stop_range_multiple: Decimal = Decimal("0.75"),
        target_range_multiple: Decimal = Decimal("1.25"),
        max_holding_bars: int = 60,
        max_entries_per_session: int = 1,
        range_width_lookback_sessions: int = 20,
        range_width_min_history_sessions: int = 0,
        min_range_width_ratio: Decimal = Decimal("0"),
        max_range_width_ratio: Decimal = Decimal("3"),
        use_vwap_filter: bool = True,
        vwap_slope_lookback: int = 10,
        trend_filter: str = "roc",
        trend_window: int = 60,
        min_trend_return: Decimal = Decimal("0"),
        exit_on_vwap_cross: bool = False,
        exit_on_trend_reversal: bool = False,
        atr_window: int = 14,
        min_opening_range_atr: Decimal = Decimal("0"),
        max_opening_range_atr: Decimal = Decimal("99"),
        use_trailing_stop: bool = False,
        trailing_atr_multiple: Decimal = Decimal("0"),
    ) -> None:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        self._mode = _Mode(str(mode).strip().lower())
        if opening_range_minutes <= 0 or opening_range_minutes >= 24 * 60:
            raise ValueError("opening_range_minutes must be between 1 and 1439")
        if max_entry_elapsed_minutes < opening_range_minutes:
            raise ValueError("max_entry_elapsed_minutes must cover the opening range")
        if minutes_before_close_flat < 0:
            raise ValueError("minutes_before_close_flat must be non-negative")
        if max_holding_bars <= 0:
            raise ValueError("max_holding_bars must be positive")
        if max_entries_per_session <= 0:
            raise ValueError("max_entries_per_session must be positive")
        if range_width_lookback_sessions < 0:
            raise ValueError("range_width_lookback_sessions must be non-negative")
        if range_width_min_history_sessions < 0:
            raise ValueError("range_width_min_history_sessions must be non-negative")
        if range_width_min_history_sessions > range_width_lookback_sessions:
            raise ValueError(
                "range_width_min_history_sessions must be <= range_width_lookback_sessions"
            )
        if not isinstance(use_vwap_filter, bool):
            raise ValueError("use_vwap_filter must be a bool")
        if not isinstance(exit_on_vwap_cross, bool):
            raise ValueError("exit_on_vwap_cross must be a bool")
        if not isinstance(exit_on_trend_reversal, bool):
            raise ValueError("exit_on_trend_reversal must be a bool")
        if not isinstance(use_trailing_stop, bool):
            raise ValueError("use_trailing_stop must be a bool")
        if vwap_slope_lookback <= 1:
            raise ValueError("vwap_slope_lookback must be greater than 1")
        if trend_window <= 0:
            raise ValueError("trend_window must be positive")
        if atr_window <= 0:
            raise ValueError("atr_window must be positive")

        normalized_quantity = Decimal(str(target_quantity))
        normalized_buffer = Decimal(str(breakout_buffer_ratio))
        normalized_stop = Decimal(str(stop_range_multiple))
        normalized_target = Decimal(str(target_range_multiple))
        normalized_min_width = Decimal(str(min_range_width_ratio))
        normalized_max_width = Decimal(str(max_range_width_ratio))
        normalized_min_trend = Decimal(str(min_trend_return))
        normalized_min_or_atr = Decimal(str(min_opening_range_atr))
        normalized_max_or_atr = Decimal(str(max_opening_range_atr))
        normalized_trailing_atr = Decimal(str(trailing_atr_multiple))
        if normalized_quantity <= Decimal("0"):
            raise ValueError("target_quantity must be positive")
        if normalized_buffer < Decimal("0"):
            raise ValueError("breakout_buffer_ratio must be non-negative")
        if normalized_stop <= Decimal("0"):
            raise ValueError("stop_range_multiple must be positive")
        if normalized_target <= Decimal("0"):
            raise ValueError("target_range_multiple must be positive")
        if normalized_min_width < Decimal("0"):
            raise ValueError("min_range_width_ratio must be non-negative")
        if normalized_max_width < normalized_min_width:
            raise ValueError("max_range_width_ratio must be >= min_range_width_ratio")
        if normalized_min_trend < Decimal("0"):
            raise ValueError("min_trend_return must be non-negative")
        if normalized_min_or_atr < Decimal("0"):
            raise ValueError("min_opening_range_atr must be non-negative")
        if normalized_max_or_atr < normalized_min_or_atr:
            raise ValueError("max_opening_range_atr must be >= min_opening_range_atr")
        if normalized_trailing_atr < Decimal("0"):
            raise ValueError("trailing_atr_multiple must be non-negative")
        if use_trailing_stop and normalized_trailing_atr <= Decimal("0"):
            raise ValueError("trailing_atr_multiple must be positive when trailing stop is enabled")

        self._symbol = normalized_symbol
        self._timeframe = str(timeframe)
        self._range_start_minutes = self._parse_et_minutes(range_start_et, name="range_start_et")
        self._session_close_minutes = self._parse_et_minutes(
            session_close_et,
            name="session_close_et",
        )
        self._opening_range_minutes = opening_range_minutes
        self._max_entry_elapsed_minutes = max_entry_elapsed_minutes
        self._minutes_before_close_flat = minutes_before_close_flat
        self._target_quantity = normalized_quantity
        self._breakout_buffer_ratio = normalized_buffer
        self._stop_range_multiple = normalized_stop
        self._target_range_multiple = normalized_target
        self._max_holding_bars = max_holding_bars
        self._max_entries_per_session = max_entries_per_session
        self._range_width_min_history_sessions = range_width_min_history_sessions
        self._min_range_width_ratio = normalized_min_width
        self._max_range_width_ratio = normalized_max_width
        self._use_vwap_filter = use_vwap_filter
        self._vwap_slope_lookback = vwap_slope_lookback
        self._trend_filter = _TrendFilter(str(trend_filter).strip().lower())
        self._trend_window = trend_window
        self._min_trend_return = normalized_min_trend
        self._exit_on_vwap_cross = exit_on_vwap_cross
        self._exit_on_trend_reversal = exit_on_trend_reversal
        self._atr_window = atr_window
        self._min_opening_range_atr = normalized_min_or_atr
        self._max_opening_range_atr = normalized_max_or_atr
        self._use_trailing_stop = use_trailing_stop
        self._trailing_atr_multiple = normalized_trailing_atr
        self._range_width_history: deque[Decimal] = deque(maxlen=range_width_lookback_sessions)
        self._asset: AssetRef | None = None
        self._indicators: _Indicators | None = None
        self._session = _SessionState()
        self._et_tz = ZoneInfo("US/Eastern")
        self._current_target = Decimal("0")
        self._entry_price: Decimal | None = None
        self._entry_width: Decimal | None = None
        self._best_favorable_price: Decimal | None = None

    def initialize(self, ctx: StrategyContext) -> None:
        self._asset = self._asset_for_symbol(ctx, self._symbol)
        ctx.subscribe(
            self._asset,
            timeframe=self._timeframe,
            warmup=max(1, self._vwap_slope_lookback, self._trend_window, self._atr_window),
        )
        self._indicators = _Indicators(
            vwap=ctx.indicator.session_vwap(self._asset),
            trend=ctx.indicator.rate_of_change(self._asset, self._trend_window),
            atr=ctx.indicator.atr(self._asset, self._atr_window),
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._asset is None or bar.instrument_id != self._asset.instrument_id:
            return
        if bar.session_id is None:
            return
        self._roll_session_if_needed(ctx, str(bar.session_id))
        self._record_vwap()
        if self._update_opening_range(bar):
            return
        if not self._session.opening_complete:
            return
        if self._current_target != Decimal("0"):
            self._manage_open_position(ctx, bar)
            return
        if self._entry_blocked(bar):
            return
        self._evaluate_entry(ctx, bar)

    def _update_opening_range(self, bar: Bar) -> bool:
        elapsed = self._elapsed_since_range_start(bar.start_time)
        if elapsed < 0 or elapsed >= self._opening_range_minutes:
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
        if elapsed + self._bar_minutes(bar) >= self._opening_range_minutes:
            self._session.opening_complete = True
        return True

    def _evaluate_entry(self, ctx: StrategyContext, bar: Bar) -> None:
        width = self._session.opening_width
        if (
            width is None
            or width <= Decimal("0")
            or self._session.opening_high is None
            or self._session.opening_low is None
            or not self._range_width_allowed(width)
            or not self._opening_range_atr_allowed(width)
        ):
            return
        buffer = width * self._breakout_buffer_ratio
        if self._mode is _Mode.BREAKOUT:
            if bar.close > self._session.opening_high + buffer:
                self._enter_if_filters_pass(
                    ctx,
                    Decimal("1"),
                    bar,
                    width,
                    reason="opening_range_breakout_long",
                )
            elif bar.close < self._session.opening_low - buffer:
                self._enter_if_filters_pass(
                    ctx,
                    Decimal("-1"),
                    bar,
                    width,
                    reason="opening_range_breakout_short",
                )
            return

        if bar.high > self._session.opening_high + buffer:
            self._session.pierced_high = True
        if bar.low < self._session.opening_low - buffer:
            self._session.pierced_low = True
        if self._session.pierced_high and bar.close < self._session.opening_high - buffer:
            self._enter_if_filters_pass(
                ctx,
                Decimal("-1"),
                bar,
                width,
                reason="opening_range_failure_short",
            )
        elif self._session.pierced_low and bar.close > self._session.opening_low + buffer:
            self._enter_if_filters_pass(
                ctx,
                Decimal("1"),
                bar,
                width,
                reason="opening_range_failure_long",
            )

    def _manage_open_position(self, ctx: StrategyContext, bar: Bar) -> None:
        self._session.bars_held += 1
        if self._near_session_close(bar):
            self._close(ctx, reason="session_close_flat")
            return
        if self._session.bars_held >= self._max_holding_bars:
            self._close(ctx, reason="max_holding_bars")
            return
        if self._entry_price is None or self._entry_width is None:
            return
        direction = Decimal("1") if self._current_target > Decimal("0") else Decimal("-1")
        if self._use_trailing_stop and self._trailing_stop_touched(direction, bar):
            self._close(ctx, reason="trailing_atr_stop")
            return
        if self._exit_on_vwap_cross and self._vwap_crossed_against_position(direction, bar):
            self._close(ctx, reason="vwap_cross_exit")
            return
        if self._exit_on_trend_reversal and self._trend_reversed(direction):
            self._close(ctx, reason="trend_reversal_exit")
            return
        move = direction * (bar.close - self._entry_price)
        if move <= -self._entry_width * self._stop_range_multiple:
            self._close(ctx, reason="range_stop")
        elif move >= self._entry_width * self._target_range_multiple:
            self._close(ctx, reason="range_target")

    def _entry_blocked(self, bar: Bar) -> bool:
        return (
            self._near_session_close(bar)
            or self._elapsed_since_range_start(bar.start_time) > self._max_entry_elapsed_minutes
            or self._session.entries >= self._max_entries_per_session
        )

    def _enter_if_filters_pass(
        self,
        ctx: StrategyContext,
        direction: Decimal,
        bar: Bar,
        width: Decimal,
        *,
        reason: str,
    ) -> None:
        if not self._entry_filters_pass(direction, bar):
            return
        self._enter(ctx, direction, bar, width, reason=reason)

    def _entry_filters_pass(self, direction: Decimal, bar: Bar) -> bool:
        indicators = self._require_indicators()
        if self._use_vwap_filter:
            vwap = self._decimal(indicators.vwap)
            slope = self._vwap_slope_sign()
            if vwap is None or slope is None:
                return False
            if direction > Decimal("0") and not (bar.close > vwap and slope > Decimal("0")):
                return False
            if direction < Decimal("0") and not (bar.close < vwap and slope < Decimal("0")):
                return False
        if self._trend_filter is _TrendFilter.ROC:
            trend = self._decimal(indicators.trend)
            if trend is None or direction * trend < self._min_trend_return:
                return False
        return True

    def _opening_range_atr_allowed(self, width: Decimal) -> bool:
        atr = self._decimal(self._require_indicators().atr)
        if atr is None or atr <= Decimal("0"):
            return False
        ratio = width / atr
        return self._min_opening_range_atr <= ratio <= self._max_opening_range_atr

    def _vwap_crossed_against_position(self, direction: Decimal, bar: Bar) -> bool:
        vwap = self._decimal(self._require_indicators().vwap)
        if vwap is None:
            return False
        if direction > Decimal("0"):
            return bar.close < vwap
        return bar.close > vwap

    def _trend_reversed(self, direction: Decimal) -> bool:
        trend = self._decimal(self._require_indicators().trend)
        return trend is not None and direction * trend < Decimal("0")

    def _trailing_stop_touched(self, direction: Decimal, bar: Bar) -> bool:
        atr = self._decimal(self._require_indicators().atr)
        if atr is None or atr <= Decimal("0"):
            return False
        if direction > Decimal("0"):
            self._best_favorable_price = (
                bar.high
                if self._best_favorable_price is None
                else max(self._best_favorable_price, bar.high)
            )
            trailing_stop = self._best_favorable_price - atr * self._trailing_atr_multiple
            return bar.close <= trailing_stop
        self._best_favorable_price = (
            bar.low
            if self._best_favorable_price is None
            else min(self._best_favorable_price, bar.low)
        )
        trailing_stop = self._best_favorable_price + atr * self._trailing_atr_multiple
        return bar.close >= trailing_stop

    def _enter(
        self,
        ctx: StrategyContext,
        direction: Decimal,
        bar: Bar,
        width: Decimal,
        *,
        reason: str,
    ) -> None:
        if self._asset is None:
            return
        target = direction * self._target_quantity
        ctx.target_quantity(
            self._asset,
            target,
            metadata={"entry_reason": reason, "session_id": str(bar.session_id)},
        )
        self._current_target = target
        self._entry_price = bar.close
        self._entry_width = width
        self._best_favorable_price = bar.close
        self._session.entries += 1
        self._session.bars_held = 0

    def _close(self, ctx: StrategyContext, *, reason: str) -> None:
        if self._asset is None or self._current_target == Decimal("0"):
            return
        ctx.close(
            self._asset,
            metadata={"exit_reason": reason, "session_id": str(self._session.session_id)},
        )
        self._current_target = Decimal("0")
        self._entry_price = None
        self._entry_width = None
        self._best_favorable_price = None
        self._session.bars_held = 0

    def _roll_session_if_needed(self, ctx: StrategyContext, session_id: str) -> None:
        if self._session.session_id is None:
            self._session = _SessionState(session_id=session_id)
            return
        if self._session.session_id == session_id:
            return
        self._close(ctx, reason="session_roll_flat")
        self._record_completed_opening_range()
        self._session = _SessionState(session_id=session_id)

    def _record_completed_opening_range(self) -> None:
        width = self._session.opening_width
        if self._session.opening_complete and width is not None and width > Decimal("0"):
            self._range_width_history.append(width)

    def _record_vwap(self) -> None:
        vwap = self._decimal(self._require_indicators().vwap)
        if vwap is not None:
            self._session.vwap_history.append(vwap)

    def _vwap_slope_sign(self) -> Decimal | None:
        history = self._session.vwap_history
        if len(history) < self._vwap_slope_lookback:
            return None
        delta = history[-1] - history[-self._vwap_slope_lookback]
        if delta == Decimal("0"):
            return Decimal("0")
        return Decimal("1") if delta > Decimal("0") else Decimal("-1")

    def _range_width_allowed(self, width: Decimal) -> bool:
        if self._range_width_min_history_sessions == 0:
            return True
        if len(self._range_width_history) < self._range_width_min_history_sessions:
            return False
        average = sum(self._range_width_history, Decimal("0")) / Decimal(
            len(self._range_width_history)
        )
        if average <= Decimal("0"):
            return False
        ratio = width / average
        return self._min_range_width_ratio <= ratio <= self._max_range_width_ratio

    def _near_session_close(self, bar: Bar) -> bool:
        minute = self._et_minute(bar.end_time)
        return 0 <= self._session_close_minutes - minute <= self._minutes_before_close_flat

    def _elapsed_since_range_start(self, timestamp: datetime) -> int:
        minute = self._et_minute(timestamp)
        return (minute - self._range_start_minutes) % (24 * 60)

    def _et_minute(self, timestamp: datetime) -> int:
        et = timestamp.astimezone(self._et_tz)
        return et.hour * 60 + et.minute

    def _require_indicators(self) -> _Indicators:
        if self._indicators is None:
            raise RuntimeError("strategy must be initialized before on_bar")
        return self._indicators

    @staticmethod
    def _bar_minutes(bar: Bar) -> int:
        seconds = (bar.end_time - bar.start_time).total_seconds()
        return max(1, int(seconds // 60))

    @staticmethod
    def _parse_et_minutes(value: str, *, name: str) -> int:
        try:
            hour_text, minute_text = str(value).split(":", maxsplit=1)
            hour = int(hour_text)
            minute = int(minute_text)
        except ValueError as exc:
            raise ValueError(f"{name} must use HH:MM") from exc
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError(f"{name} must use HH:MM")
        return hour * 60 + minute

    @staticmethod
    def _decimal(indicator: AssetIndicator) -> Decimal | None:
        value = indicator.value
        return value if isinstance(value, Decimal) else None

    @staticmethod
    def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
        try:
            return ctx.future(symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(symbol)


__all__ = ["OrbVwapTrendFilterStrategy"]
