"""VWAP pullback + rejection v2 — state-machine implementation.

Replaces the OPT-75/76/77/78 ``vwap_pullback.py`` after research surfaced
that the L1/L2/L3 score system mixed three unrelated strategies
(MA stacking + opening range breakout + VWAP pullback), masked the
rejection-confirmation requirement, and made the trailing stop the
de-facto exit driver. This v2 follows Brian Shannon's anchored-VWAP
framework:

  1. Trend confirmed by rising session VWAP slope.
  2. Pullback toward VWAP detected over multiple bars.
  3. Rejection confirmed by a green close back above VWAP with
     volume support (the "confirmation candle").
  4. Enter on the bar AFTER confirmation; stop just below the
     pullback swing low; targets at VWAP +1σ and +2σ.
  5. Exit when the thesis fails (``close < VWAP``), the +2σ band
     is hit, or 30 minutes before session close.

Chop filter (first-hour VWAP crossings ≤ N) and a time-of-day filter
(only the configured US-Eastern hours) prevent trading during the
low-liquidity 24h overnight noise that dominated GC backtests.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetIndicator, AssetRef, Strategy, StrategyContext


class _State(StrEnum):
    IDLE = "idle"
    WAIT_PULLBACK = "wait_pullback"
    WAIT_REJECTION = "wait_rejection"
    ENTERED = "entered"


_Direction = StrEnum("_Direction", {"LONG": "long", "SHORT": "short"})


@dataclass(frozen=True, slots=True)
class VwapPullbackV2Config:
    """Tunable parameters for the v2 VWAP pullback strategy."""

    symbol: str = "GC"
    atr_window: int = 14
    volume_ratio_window: int = 20

    # Trend filter
    vwap_slope_lookback: int = 10
    require_vwap_slope_positive: bool = True

    # Pullback zone (around VWAP)
    pullback_touch_atr_below: Decimal = Decimal("0.3")
    pullback_touch_atr_above: Decimal = Decimal("0.1")
    max_pullback_break_atr: Decimal = Decimal("1.0")

    # Rejection confirmation
    min_volume_ratio: Decimal = Decimal("1.2")

    # Staleness
    max_bars_in_wait_state: int = 10

    # Sizing
    target_quantity: Decimal = Decimal("1")

    # Stops & targets
    stop_buffer_atr: Decimal = Decimal("0.2")

    # Time-of-day filter (US/Eastern hours, half-open [start, end)).
    # Disable this to rely on exchange session bars, e.g. GC [ET 18:00, ET 17:00).
    use_trading_hours_filter: bool = True
    trading_hours_et_start: int = 8
    trading_hours_et_end: int = 16

    # Chop filter
    max_first_hour_vwap_crossings: int = 3
    first_hour_minutes: int = 60

    # Session-close defensive flat
    minutes_before_close_flat: int = 30
    session_close_et_hour: int = 17
    session_close_et_minute: int = 0

    def __post_init__(self) -> None:
        positive_ints = {
            "atr_window": self.atr_window,
            "volume_ratio_window": self.volume_ratio_window,
            "vwap_slope_lookback": self.vwap_slope_lookback,
            "max_bars_in_wait_state": self.max_bars_in_wait_state,
            "max_first_hour_vwap_crossings": self.max_first_hour_vwap_crossings,
            "first_hour_minutes": self.first_hour_minutes,
            "minutes_before_close_flat": self.minutes_before_close_flat,
        }
        for name, value in positive_ints.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        # All decimal fields are coerced; positivity requirements differ.
        strict_positive_decimals = (
            "pullback_touch_atr_below",
            "max_pullback_break_atr",
            "target_quantity",
        )
        non_negative_decimals = (
            "pullback_touch_atr_above",
            "min_volume_ratio",
            "stop_buffer_atr",
        )
        for name in (*strict_positive_decimals, *non_negative_decimals):
            current = getattr(self, name)
            if not isinstance(current, Decimal):
                object.__setattr__(self, name, Decimal(str(current)))
        for name in strict_positive_decimals:
            if getattr(self, name) <= Decimal("0"):
                raise ValueError(f"{name} must be positive")
        for name in non_negative_decimals:
            if getattr(self, name) < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if not isinstance(self.use_trading_hours_filter, bool):
            raise ValueError("use_trading_hours_filter must be a bool")
        if not (0 <= self.trading_hours_et_start < 24):
            raise ValueError("trading_hours_et_start must be 0..23")
        if not (0 < self.trading_hours_et_end <= 24):
            raise ValueError("trading_hours_et_end must be 1..24")
        if (
            self.use_trading_hours_filter
            and self.trading_hours_et_start >= self.trading_hours_et_end
        ):
            raise ValueError("trading_hours_et_start must be < trading_hours_et_end")


@dataclass(slots=True)
class _SessionState:
    """Per-session running state — reset on session_id change."""

    session_id: str | None = None
    bars_seen: int = 0
    first_hour_crossings: int = 0
    last_vwap_sign: int = 0
    sum_var_x_vol: Decimal = Decimal("0")
    sum_vol: Decimal = Decimal("0")
    vwap_history: deque[Decimal] = field(default_factory=deque)


class VwapPullbackV2Strategy(Strategy):
    """State-machine VWAP pullback + rejection."""

    def __init__(self, config: VwapPullbackV2Config | None = None, **overrides: Any) -> None:
        if config is not None and overrides:
            raise ValueError("pass either config or overrides, not both")
        self._config = config if config is not None else VwapPullbackV2Config(**overrides)
        self._asset: AssetRef | None = None
        self._vwap: AssetIndicator | None = None
        self._atr: AssetIndicator | None = None
        self._volume_ratio: AssetIndicator | None = None
        self._state: _State = _State.IDLE
        self._direction: _Direction | None = None
        self._trend_high: Decimal | None = None
        self._trend_low: Decimal | None = None
        self._pullback_low: Decimal | None = None
        self._pullback_high: Decimal | None = None
        self._bars_in_wait: int = 0
        self._entry_price: Decimal | None = None
        self._stop_price: Decimal | None = None
        self._target_1: Decimal | None = None
        self._target_2: Decimal | None = None
        self._session = _SessionState()
        self._et_tz = ZoneInfo("US/Eastern")

    @property
    def state(self) -> _State:
        return self._state

    @property
    def session_sigma(self) -> Decimal | None:
        if self._session.sum_vol == Decimal("0"):
            return None
        variance = self._session.sum_var_x_vol / self._session.sum_vol
        if variance <= Decimal("0"):
            return Decimal("0")
        # Decimal-friendly sqrt
        return variance.sqrt()

    def initialize(self, ctx: StrategyContext) -> None:
        self._asset = ctx.symbol(self._config.symbol)
        self._vwap = ctx.indicator.session_vwap(self._asset)
        self._atr = ctx.indicator.atr(self._asset, self._config.atr_window)
        self._volume_ratio = ctx.indicator.volume_ratio(
            self._asset, self._config.volume_ratio_window
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._asset is None or self._vwap is None or self._atr is None:
            raise RuntimeError("strategy must be initialized before on_bar")

        self._update_session_state(bar)

        if not self._indicators_ready():
            return

        vwap = self._decimal_value(self._vwap)
        atr = self._decimal_value(self._atr)
        if vwap is None or atr is None or atr <= Decimal("0"):
            return

        # Defensive session-close flat
        if self._state == _State.ENTERED and self._near_session_close(bar):
            self._exit_position(ctx, reason="session_close")
            return

        # Apply state machine
        if self._state == _State.IDLE:
            self._step_idle(bar, vwap, atr)
        elif self._state == _State.WAIT_PULLBACK:
            self._step_wait_pullback(bar, vwap, atr)
        elif self._state == _State.WAIT_REJECTION:
            self._step_wait_rejection(ctx, bar, vwap, atr)
        elif self._state == _State.ENTERED:
            self._step_entered(ctx, bar, vwap)

    def _step_idle(self, bar: Bar, vwap: Decimal, atr: Decimal) -> None:
        if not self._in_trading_hours(bar):
            return
        if self._is_chop_day():
            return
        slope_up = self._vwap_slope_positive()
        if self._config.require_vwap_slope_positive and slope_up is None:
            return
        if slope_up is True and bar.close > vwap:
            self._enter_state(_State.WAIT_PULLBACK, direction=_Direction.LONG)
            self._trend_high = bar.high
            return
        if slope_up is False and bar.close < vwap:
            self._enter_state(_State.WAIT_PULLBACK, direction=_Direction.SHORT)
            self._trend_low = bar.low
            return

    def _step_wait_pullback(self, bar: Bar, vwap: Decimal, atr: Decimal) -> None:
        self._bars_in_wait += 1
        if self._bars_in_wait > self._config.max_bars_in_wait_state:
            self._reset_to_idle()
            return
        if not self._in_trading_hours(bar):
            self._reset_to_idle()
            return
        if self._direction is _Direction.LONG:
            self._trend_high = max(self._trend_high or bar.high, bar.high)
            # Thesis broken: too far below VWAP
            if bar.close < vwap - atr * self._config.max_pullback_break_atr:
                self._reset_to_idle()
                return
            # Pullback touch: bar.low entered the zone around VWAP
            touch_floor = vwap - atr * self._config.pullback_touch_atr_below
            touch_ceiling = vwap + atr * self._config.pullback_touch_atr_above
            if touch_floor <= bar.low <= touch_ceiling:
                self._pullback_low = bar.low
                self._enter_state(_State.WAIT_REJECTION, direction=self._direction)
        else:  # SHORT
            self._trend_low = min(self._trend_low or bar.low, bar.low)
            if bar.close > vwap + atr * self._config.max_pullback_break_atr:
                self._reset_to_idle()
                return
            touch_ceiling = vwap + atr * self._config.pullback_touch_atr_below
            touch_floor = vwap - atr * self._config.pullback_touch_atr_above
            if touch_floor <= bar.high <= touch_ceiling:
                self._pullback_high = bar.high
                # SHORT path; self._direction is guaranteed by the branch above.
                assert self._direction is not None
                self._enter_state(_State.WAIT_REJECTION, direction=self._direction)

    def _step_wait_rejection(
        self, ctx: StrategyContext, bar: Bar, vwap: Decimal, atr: Decimal
    ) -> None:
        self._bars_in_wait += 1
        if self._bars_in_wait > self._config.max_bars_in_wait_state:
            self._reset_to_idle()
            return
        # Thesis broken: closes too far on the wrong side of VWAP
        if self._direction is _Direction.LONG:
            self._pullback_low = min(self._pullback_low or bar.low, bar.low)
            if bar.close < vwap - atr * self._config.max_pullback_break_atr:
                self._reset_to_idle()
                return
            if self._is_long_rejection_confirmed(bar, vwap):
                self._enter_position(ctx, bar, vwap, atr)
        else:
            self._pullback_high = max(self._pullback_high or bar.high, bar.high)
            if bar.close > vwap + atr * self._config.max_pullback_break_atr:
                self._reset_to_idle()
                return
            if self._is_short_rejection_confirmed(bar, vwap):
                self._enter_position(ctx, bar, vwap, atr)

    def _step_entered(self, ctx: StrategyContext, bar: Bar, vwap: Decimal) -> None:
        if self._direction is _Direction.LONG:
            # Thesis failure: close back below VWAP
            if bar.close < vwap:
                self._exit_position(ctx, reason="thesis_failed_close_below_vwap")
                return
            # Stop hit
            if self._stop_price is not None and bar.low <= self._stop_price:
                self._exit_position(ctx, reason="stop")
                return
            # Target 2 reached
            if self._target_2 is not None and bar.high >= self._target_2:
                self._exit_position(ctx, reason="target_2_sigma")
                return
        else:
            if bar.close > vwap:
                self._exit_position(ctx, reason="thesis_failed_close_above_vwap")
                return
            if self._stop_price is not None and bar.high >= self._stop_price:
                self._exit_position(ctx, reason="stop")
                return
            if self._target_2 is not None and bar.low <= self._target_2:
                self._exit_position(ctx, reason="target_2_sigma")
                return

    def _is_long_rejection_confirmed(self, bar: Bar, vwap: Decimal) -> bool:
        if bar.close <= vwap:
            return False
        if bar.close <= bar.open:
            return False
        vol_ratio = self._decimal_value(self._volume_ratio)
        if vol_ratio is None or vol_ratio < self._config.min_volume_ratio:
            return False
        return True

    def _is_short_rejection_confirmed(self, bar: Bar, vwap: Decimal) -> bool:
        if bar.close >= vwap:
            return False
        if bar.close >= bar.open:
            return False
        vol_ratio = self._decimal_value(self._volume_ratio)
        if vol_ratio is None or vol_ratio < self._config.min_volume_ratio:
            return False
        return True

    def _enter_position(self, ctx: StrategyContext, bar: Bar, vwap: Decimal, atr: Decimal) -> None:
        if self._asset is None:
            return
        sigma = self.session_sigma or atr  # Fall back to ATR if sigma not yet meaningful
        self._entry_price = bar.close
        if self._direction is _Direction.LONG:
            self._stop_price = (self._pullback_low or bar.low) - atr * self._config.stop_buffer_atr
            self._target_1 = vwap + sigma
            self._target_2 = vwap + sigma * Decimal("2")
            ctx.target_quantity(self._asset, self._config.target_quantity)
        else:
            self._stop_price = (
                self._pullback_high or bar.high
            ) + atr * self._config.stop_buffer_atr
            self._target_1 = vwap - sigma
            self._target_2 = vwap - sigma * Decimal("2")
            ctx.target_quantity(self._asset, -self._config.target_quantity)
        self._state = _State.ENTERED
        self._bars_in_wait = 0

    def _exit_position(self, ctx: StrategyContext, *, reason: str) -> None:
        _ = reason  # plumbing point — could be logged via ctx in a future iteration
        if self._asset is not None:
            ctx.close(self._asset)
        self._clear_position_state()

    def _clear_position_state(self) -> None:
        self._state = _State.IDLE
        self._direction = None
        self._trend_high = None
        self._trend_low = None
        self._pullback_low = None
        self._pullback_high = None
        self._entry_price = None
        self._stop_price = None
        self._target_1 = None
        self._target_2 = None
        self._bars_in_wait = 0

    def _enter_state(self, state: _State, *, direction: _Direction) -> None:
        self._state = state
        self._direction = direction
        self._bars_in_wait = 0

    def _reset_to_idle(self) -> None:
        self._clear_position_state()

    def _update_session_state(self, bar: Bar) -> None:
        session_id = str(bar.session_id)
        if session_id != self._session.session_id:
            self._session = _SessionState(session_id=session_id)
        s = self._session
        s.bars_seen += 1

        # Track VWAP history for slope
        vwap = self._decimal_value(self._vwap) if self._vwap is not None else None
        if vwap is not None:
            s.vwap_history.append(vwap)
            max_history = self._config.vwap_slope_lookback + 1
            while len(s.vwap_history) > max_history:
                s.vwap_history.popleft()

            # Track VWAP crossings during first hour
            current_sign = 1 if bar.close > vwap else (-1 if bar.close < vwap else 0)
            if s.bars_seen <= self._config.first_hour_minutes:
                if s.last_vwap_sign != 0 and current_sign != 0 and current_sign != s.last_vwap_sign:
                    s.first_hour_crossings += 1
            s.last_vwap_sign = current_sign

            # Volume-weighted variance for σ-band
            deviation = bar.close - vwap
            s.sum_var_x_vol += deviation * deviation * bar.volume
            s.sum_vol += bar.volume

    def _vwap_slope_positive(self) -> bool | None:
        """Return True (rising), False (falling), None (insufficient history)."""
        if len(self._session.vwap_history) <= self._config.vwap_slope_lookback:
            return None
        recent = self._session.vwap_history[-1]
        anchor = self._session.vwap_history[-self._config.vwap_slope_lookback - 1]
        return recent > anchor if recent != anchor else None  # exactly flat → None

    def _is_chop_day(self) -> bool:
        if self._session.bars_seen < self._config.first_hour_minutes:
            return False
        return self._session.first_hour_crossings > self._config.max_first_hour_vwap_crossings

    def _in_trading_hours(self, bar: Bar) -> bool:
        if not self._config.use_trading_hours_filter:
            return True
        # Compare in minutes-of-day so end=24 (end of day) is expressible.
        et_dt = bar.start_time.astimezone(self._et_tz)
        bar_minutes = et_dt.hour * 60 + et_dt.minute
        start_minutes = self._config.trading_hours_et_start * 60
        end_minutes = self._config.trading_hours_et_end * 60
        return start_minutes <= bar_minutes < end_minutes

    def _near_session_close(self, bar: Bar) -> bool:
        et_time = bar.start_time.astimezone(self._et_tz).time()
        close_hour = self._config.session_close_et_hour
        close_minute = self._config.session_close_et_minute
        # Compare in minutes-of-day
        bar_minutes = et_time.hour * 60 + et_time.minute
        close_minutes = close_hour * 60 + close_minute
        return 0 <= close_minutes - bar_minutes <= self._config.minutes_before_close_flat

    def _indicators_ready(self) -> bool:
        for ind in (self._vwap, self._atr, self._volume_ratio):
            if ind is None or not ind.ready or ind.value is None:
                return False
        return True

    @staticmethod
    def _decimal_value(indicator: AssetIndicator | None) -> Decimal | None:
        if indicator is None or indicator.value is None:
            return None
        value = indicator.value
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))


__all__ = ["VwapPullbackV2Config", "VwapPullbackV2Strategy"]
