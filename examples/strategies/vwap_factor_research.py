"""Research-only VWAP pullback strategy with configurable indicator gates.

This module intentionally lives under ``examples``. It is a strategy-lab
surface for comparing VWAP pullback variants through the normal Strategy SDK
and backtest runner without changing the production VWAP v2 strategy.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.indicators.technical import (
    BollingerBandsValue,
    DirectionalMovementValue,
    DonchianChannelValue,
    KeltnerChannelValue,
    MACDValue,
    StochasticOscillatorValue,
)
from qts.strategy_sdk import AssetIndicator, AssetRef, Strategy, StrategyContext


class _State(StrEnum):
    IDLE = "idle"
    WAIT_PULLBACK = "wait_pullback"
    WAIT_REJECTION = "wait_rejection"
    ENTERED = "entered"


class _Direction(StrEnum):
    LONG = "long"
    SHORT = "short"


class _ExitReason(StrEnum):
    SESSION_CLOSE_FLAT = "session_close_flat"
    LONG_CLOSE_BELOW_VWAP = "long_close_below_vwap"
    SHORT_CLOSE_ABOVE_VWAP = "short_close_above_vwap"
    LONG_STOP_ATR_TOUCHED = "long_stop_atr_touched"
    SHORT_STOP_ATR_TOUCHED = "short_stop_atr_touched"
    LONG_TARGET_R_TOUCHED = "long_target_r_touched"
    SHORT_TARGET_R_TOUCHED = "short_target_r_touched"


@dataclass(frozen=True, slots=True)
class VwapFactorResearchConfig:
    """Configuration for one research candidate."""

    symbol: str = "GC"
    target_quantity: Decimal = Decimal("1")

    atr_window: int = 14
    volume_ratio_window: int = 20
    vwap_slope_lookback: int = 5
    max_bars_in_wait_state: int = 5

    pullback_touch_atr_below: Decimal = Decimal("0.2")
    pullback_touch_atr_above: Decimal = Decimal("0.1")
    max_pullback_break_atr: Decimal = Decimal("1.0")
    min_volume_ratio: Decimal = Decimal("1.2")
    stop_buffer_atr: Decimal = Decimal("0.2")
    stop_atr_multiple: Decimal = Decimal("1")
    target_r_multiple: Decimal = Decimal("2")
    exit_on_vwap_cross: bool = False

    time_window: str = "current_08_16"
    factor_filters: tuple[str, ...] = ()

    distance_min_atr: Decimal = Decimal("0")
    distance_max_atr: Decimal = Decimal("99")
    volume_ratio_min: Decimal = Decimal("0")
    volume_ratio_max: Decimal = Decimal("99")
    adx_min: Decimal = Decimal("18")
    rsi_min: Decimal = Decimal("35")
    rsi_max: Decimal = Decimal("65")
    mfi_min: Decimal = Decimal("35")
    mfi_max: Decimal = Decimal("65")
    cmf_min: Decimal = Decimal("0")
    roc_min_abs: Decimal = Decimal("0")
    cci_abs_min: Decimal = Decimal("50")
    stochastic_min: Decimal = Decimal("20")
    stochastic_max: Decimal = Decimal("80")
    williams_r_min: Decimal = Decimal("-80")
    williams_r_max: Decimal = Decimal("-20")
    max_bollinger_z_abs: Decimal = Decimal("1.5")
    vwap_slope_min_atr: Decimal = Decimal("0")
    atr_pct_min: Decimal = Decimal("0")
    atr_pct_max: Decimal = Decimal("99")
    session_sigma_min_atr: Decimal = Decimal("0")
    session_sigma_max_atr: Decimal = Decimal("99")
    rth_drive_min_atr: Decimal = Decimal("0")

    rsi_window: int = 14
    adx_window: int = 14
    mfi_window: int = 14
    cmf_window: int = 20
    roc_window: int = 15
    ts_momentum_60_window: int = 60
    ts_momentum_120_window: int = 120
    ts_momentum_240_window: int = 240
    cci_window: int = 20
    stochastic_window: int = 14
    williams_window: int = 14
    bollinger_window: int = 20
    donchian_window: int = 20
    donchian_long_window: int = 60
    keltner_window: int = 20
    sma_fast_window: int = 20
    sma_slow_window: int = 80
    sma_long_fast_window: int = 50
    sma_long_slow_window: int = 200
    macd_fast_window: int = 12
    macd_slow_window: int = 26
    macd_signal_window: int = 9
    technical_score_min: int = 4
    oscillator_score_min: int = 4
    volume_curve_lookback_sessions: int = 20

    ts_momentum_min_abs: Decimal = Decimal("0")
    volume_curve_ratio_min: Decimal = Decimal("0.6")
    volume_curve_ratio_max: Decimal = Decimal("1.8")
    minutes_before_close_flat: int = 30
    session_close_et_hour: int = 17
    session_close_et_minute: int = 0

    def __post_init__(self) -> None:
        positive_ints = {
            "atr_window": self.atr_window,
            "volume_ratio_window": self.volume_ratio_window,
            "vwap_slope_lookback": self.vwap_slope_lookback,
            "max_bars_in_wait_state": self.max_bars_in_wait_state,
            "rsi_window": self.rsi_window,
            "adx_window": self.adx_window,
            "mfi_window": self.mfi_window,
            "cmf_window": self.cmf_window,
            "roc_window": self.roc_window,
            "ts_momentum_60_window": self.ts_momentum_60_window,
            "ts_momentum_120_window": self.ts_momentum_120_window,
            "ts_momentum_240_window": self.ts_momentum_240_window,
            "cci_window": self.cci_window,
            "stochastic_window": self.stochastic_window,
            "williams_window": self.williams_window,
            "bollinger_window": self.bollinger_window,
            "donchian_window": self.donchian_window,
            "donchian_long_window": self.donchian_long_window,
            "keltner_window": self.keltner_window,
            "sma_fast_window": self.sma_fast_window,
            "sma_slow_window": self.sma_slow_window,
            "sma_long_fast_window": self.sma_long_fast_window,
            "sma_long_slow_window": self.sma_long_slow_window,
            "macd_fast_window": self.macd_fast_window,
            "macd_slow_window": self.macd_slow_window,
            "macd_signal_window": self.macd_signal_window,
            "technical_score_min": self.technical_score_min,
            "oscillator_score_min": self.oscillator_score_min,
            "volume_curve_lookback_sessions": self.volume_curve_lookback_sessions,
            "minutes_before_close_flat": self.minutes_before_close_flat,
        }
        for name, value in positive_ints.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        decimal_fields = (
            "target_quantity",
            "pullback_touch_atr_below",
            "pullback_touch_atr_above",
            "max_pullback_break_atr",
            "min_volume_ratio",
            "stop_buffer_atr",
            "stop_atr_multiple",
            "target_r_multiple",
            "distance_min_atr",
            "distance_max_atr",
            "volume_ratio_min",
            "volume_ratio_max",
            "adx_min",
            "rsi_min",
            "rsi_max",
            "mfi_min",
            "mfi_max",
            "cmf_min",
            "roc_min_abs",
            "cci_abs_min",
            "stochastic_min",
            "stochastic_max",
            "williams_r_min",
            "williams_r_max",
            "max_bollinger_z_abs",
            "vwap_slope_min_atr",
            "atr_pct_min",
            "atr_pct_max",
            "session_sigma_min_atr",
            "session_sigma_max_atr",
            "rth_drive_min_atr",
            "ts_momentum_min_abs",
            "volume_curve_ratio_min",
            "volume_curve_ratio_max",
        )
        for name in decimal_fields:
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                object.__setattr__(self, name, Decimal(str(value)))
        if isinstance(self.exit_on_vwap_cross, str):
            object.__setattr__(
                self,
                "exit_on_vwap_cross",
                self.exit_on_vwap_cross.strip().lower() in {"1", "true", "yes", "on"},
            )
        if isinstance(self.factor_filters, str):
            object.__setattr__(self, "factor_filters", (self.factor_filters,))
        elif not isinstance(self.factor_filters, tuple):
            object.__setattr__(
                self,
                "factor_filters",
                tuple(str(item) for item in self.factor_filters),
            )
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if self.target_quantity <= Decimal("0"):
            raise ValueError("target_quantity must be positive")
        if self.pullback_touch_atr_below <= Decimal("0"):
            raise ValueError("pullback_touch_atr_below must be positive")
        if self.max_pullback_break_atr <= Decimal("0"):
            raise ValueError("max_pullback_break_atr must be positive")
        if self.stop_atr_multiple <= Decimal("0"):
            raise ValueError("stop_atr_multiple must be positive")
        if self.target_r_multiple <= Decimal("0"):
            raise ValueError("target_r_multiple must be positive")
        if self.distance_min_atr > self.distance_max_atr:
            raise ValueError("distance_min_atr must be <= distance_max_atr")
        if self.volume_ratio_min > self.volume_ratio_max:
            raise ValueError("volume_ratio_min must be <= volume_ratio_max")
        if self.atr_pct_min > self.atr_pct_max:
            raise ValueError("atr_pct_min must be <= atr_pct_max")
        if self.session_sigma_min_atr > self.session_sigma_max_atr:
            raise ValueError("session_sigma_min_atr must be <= session_sigma_max_atr")
        if self.macd_fast_window >= self.macd_slow_window:
            raise ValueError("macd_fast_window must be < macd_slow_window")
        if self.sma_fast_window >= self.sma_slow_window:
            raise ValueError("sma_fast_window must be < sma_slow_window")
        if self.sma_long_fast_window >= self.sma_long_slow_window:
            raise ValueError("sma_long_fast_window must be < sma_long_slow_window")
        if self.volume_curve_ratio_min > self.volume_curve_ratio_max:
            raise ValueError("volume_curve_ratio_min must be <= volume_curve_ratio_max")


@dataclass(slots=True)
class _SessionState:
    session_id: str | None = None
    sum_var_x_vol: Decimal = Decimal("0")
    sum_vol: Decimal = Decimal("0")
    vwap_history: deque[Decimal] = field(default_factory=deque)
    rth_open: Decimal | None = None
    rth_drive: Decimal | None = None


@dataclass(slots=True)
class _Indicators:
    vwap: AssetIndicator
    atr: AssetIndicator
    volume_ratio: AssetIndicator
    rsi: AssetIndicator
    adx: AssetIndicator
    mfi: AssetIndicator
    cmf: AssetIndicator
    roc: AssetIndicator
    roc_60: AssetIndicator
    roc_120: AssetIndicator
    roc_240: AssetIndicator
    cci: AssetIndicator
    stochastic: AssetIndicator
    williams_r: AssetIndicator
    bollinger: AssetIndicator
    donchian: AssetIndicator
    donchian_long: AssetIndicator
    keltner: AssetIndicator
    sma_fast: AssetIndicator
    sma_slow: AssetIndicator
    sma_long_fast: AssetIndicator
    sma_long_slow: AssetIndicator
    macd: AssetIndicator


class VwapFactorResearchStrategy(Strategy):
    """VWAP pullback entry with research-only indicator gates."""

    def __init__(
        self,
        config: VwapFactorResearchConfig | None = None,
        **overrides: Any,
    ) -> None:
        if config is not None and overrides:
            raise ValueError("pass either config or overrides, not both")
        self._config = config if config is not None else VwapFactorResearchConfig(**overrides)
        self._asset: AssetRef | None = None
        self._indicators: _Indicators | None = None
        self._state: _State = _State.IDLE
        self._direction: _Direction | None = None
        self._pullback_low: Decimal | None = None
        self._pullback_high: Decimal | None = None
        self._bars_in_wait = 0
        self._entry_price: Decimal | None = None
        self._stop_price: Decimal | None = None
        self._target_2: Decimal | None = None
        self._session = _SessionState()
        self._et_tz = ZoneInfo("US/Eastern")
        self._volume_curve_history: dict[int, deque[Decimal]] = {}

    def initialize(self, ctx: StrategyContext) -> None:
        asset = ctx.symbol(self._config.symbol)
        self._asset = asset
        self._indicators = _Indicators(
            vwap=ctx.indicator.session_vwap(asset),
            atr=ctx.indicator.atr(asset, self._config.atr_window),
            volume_ratio=ctx.indicator.volume_ratio(asset, self._config.volume_ratio_window),
            rsi=ctx.indicator.rsi(asset, self._config.rsi_window),
            adx=ctx.indicator.adx(asset, self._config.adx_window),
            mfi=ctx.indicator.money_flow_index(asset, self._config.mfi_window),
            cmf=ctx.indicator.chaikin_money_flow(asset, self._config.cmf_window),
            roc=ctx.indicator.rate_of_change(asset, self._config.roc_window),
            roc_60=ctx.indicator.rate_of_change(asset, self._config.ts_momentum_60_window),
            roc_120=ctx.indicator.rate_of_change(asset, self._config.ts_momentum_120_window),
            roc_240=ctx.indicator.rate_of_change(asset, self._config.ts_momentum_240_window),
            cci=ctx.indicator.cci(asset, self._config.cci_window),
            stochastic=ctx.indicator.stochastic(asset, self._config.stochastic_window),
            williams_r=ctx.indicator.williams_r(asset, self._config.williams_window),
            bollinger=ctx.indicator.bollinger_bands(asset, self._config.bollinger_window),
            donchian=ctx.indicator.donchian_channel(asset, self._config.donchian_window),
            donchian_long=ctx.indicator.donchian_channel(asset, self._config.donchian_long_window),
            keltner=ctx.indicator.keltner_channel(asset, self._config.keltner_window),
            sma_fast=ctx.indicator.sma(asset, self._config.sma_fast_window),
            sma_slow=ctx.indicator.sma(asset, self._config.sma_slow_window),
            sma_long_fast=ctx.indicator.sma(asset, self._config.sma_long_fast_window),
            sma_long_slow=ctx.indicator.sma(asset, self._config.sma_long_slow_window),
            macd=ctx.indicator.macd(
                asset,
                self._config.macd_fast_window,
                self._config.macd_slow_window,
                self._config.macd_signal_window,
            ),
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        indicators = self._require_indicators()
        self._update_session_state(bar)
        if not self._core_ready(indicators):
            return
        vwap = self._decimal(indicators.vwap)
        atr = self._decimal(indicators.atr)
        if vwap is None or atr is None or atr <= Decimal("0"):
            return
        if self._state == _State.ENTERED and self._near_session_close(bar):
            self._exit(ctx, _ExitReason.SESSION_CLOSE_FLAT)
            return
        if self._state == _State.IDLE:
            self._step_idle(bar, vwap)
        elif self._state == _State.WAIT_PULLBACK:
            self._step_wait_pullback(bar, vwap, atr)
        elif self._state == _State.WAIT_REJECTION:
            self._step_wait_rejection(ctx, bar, vwap, atr)
        elif self._state == _State.ENTERED:
            self._step_entered(ctx, bar, vwap)

    def _step_idle(self, bar: Bar, vwap: Decimal) -> None:
        if not self._time_allowed(bar):
            return
        slope_up = self._vwap_slope_positive()
        if slope_up is True and bar.close > vwap:
            self._enter_state(_State.WAIT_PULLBACK, _Direction.LONG)
        elif slope_up is False and bar.close < vwap:
            self._enter_state(_State.WAIT_PULLBACK, _Direction.SHORT)

    def _step_wait_pullback(self, bar: Bar, vwap: Decimal, atr: Decimal) -> None:
        self._bars_in_wait += 1
        if self._bars_in_wait > self._config.max_bars_in_wait_state:
            self._reset()
            return
        if not self._time_allowed(bar):
            self._reset()
            return
        if self._direction is _Direction.LONG:
            if bar.close < vwap - atr * self._config.max_pullback_break_atr:
                self._reset()
                return
            if (
                vwap - atr * self._config.pullback_touch_atr_below
                <= bar.low
                <= vwap + atr * self._config.pullback_touch_atr_above
            ):
                self._pullback_low = bar.low
                self._enter_state(_State.WAIT_REJECTION, _Direction.LONG)
        else:
            if bar.close > vwap + atr * self._config.max_pullback_break_atr:
                self._reset()
                return
            if (
                vwap - atr * self._config.pullback_touch_atr_above
                <= bar.high
                <= vwap + atr * self._config.pullback_touch_atr_below
            ):
                self._pullback_high = bar.high
                self._enter_state(_State.WAIT_REJECTION, _Direction.SHORT)

    def _step_wait_rejection(
        self,
        ctx: StrategyContext,
        bar: Bar,
        vwap: Decimal,
        atr: Decimal,
    ) -> None:
        self._bars_in_wait += 1
        if self._bars_in_wait > self._config.max_bars_in_wait_state:
            self._reset()
            return
        if self._direction is _Direction.LONG:
            self._pullback_low = min(self._pullback_low or bar.low, bar.low)
            if bar.close < vwap - atr * self._config.max_pullback_break_atr:
                self._reset()
                return
            if self._long_rejection(bar, vwap) and self._factor_filters_pass(bar, vwap, atr):
                self._enter_position(ctx, bar, vwap, atr)
        else:
            self._pullback_high = max(self._pullback_high or bar.high, bar.high)
            if bar.close > vwap + atr * self._config.max_pullback_break_atr:
                self._reset()
                return
            if self._short_rejection(bar, vwap) and self._factor_filters_pass(bar, vwap, atr):
                self._enter_position(ctx, bar, vwap, atr)

    def _step_entered(self, ctx: StrategyContext, bar: Bar, vwap: Decimal) -> None:
        if self._direction is _Direction.LONG:
            if self._config.exit_on_vwap_cross and bar.close < vwap:
                self._exit(ctx, _ExitReason.LONG_CLOSE_BELOW_VWAP)
            elif self._stop_price is not None and bar.low <= self._stop_price:
                self._exit(ctx, _ExitReason.LONG_STOP_ATR_TOUCHED)
            elif self._target_2 is not None and bar.high >= self._target_2:
                self._exit(ctx, _ExitReason.LONG_TARGET_R_TOUCHED)
        else:
            if self._config.exit_on_vwap_cross and bar.close > vwap:
                self._exit(ctx, _ExitReason.SHORT_CLOSE_ABOVE_VWAP)
            elif self._stop_price is not None and bar.high >= self._stop_price:
                self._exit(ctx, _ExitReason.SHORT_STOP_ATR_TOUCHED)
            elif self._target_2 is not None and bar.low <= self._target_2:
                self._exit(ctx, _ExitReason.SHORT_TARGET_R_TOUCHED)

    def _enter_position(
        self,
        ctx: StrategyContext,
        bar: Bar,
        vwap: Decimal,
        atr: Decimal,
    ) -> None:
        if self._asset is None:
            return
        self._entry_price = bar.close
        stop_distance = atr * self._config.stop_atr_multiple
        target_distance = stop_distance * self._config.target_r_multiple
        if self._direction is _Direction.LONG:
            self._stop_price = self._entry_price - stop_distance
            self._target_2 = self._entry_price + target_distance
            ctx.target_quantity(self._asset, self._config.target_quantity)
        else:
            self._stop_price = self._entry_price + stop_distance
            self._target_2 = self._entry_price - target_distance
            ctx.target_quantity(self._asset, -self._config.target_quantity)
        self._state = _State.ENTERED
        self._bars_in_wait = 0

    def _factor_filters_pass(self, bar: Bar, vwap: Decimal, atr: Decimal) -> bool:
        for filter_name in self._config.factor_filters:
            if not self._factor_filter_passes(filter_name, bar, vwap, atr):
                return False
        return True

    def _factor_filter_passes(
        self,
        filter_name: str,
        bar: Bar,
        vwap: Decimal,
        atr: Decimal,
    ) -> bool:
        indicators = self._require_indicators()
        direction = self._direction_sign()
        if filter_name == "distance_mid":
            distance = abs(bar.close - vwap) / atr
            return self._config.distance_min_atr <= distance <= self._config.distance_max_atr
        if filter_name == "volume_range":
            volume_ratio = self._decimal(indicators.volume_ratio)
            return (
                volume_ratio is not None
                and self._config.volume_ratio_min <= volume_ratio <= self._config.volume_ratio_max
            )
        if filter_name == "volume_le":
            volume_ratio = self._decimal(indicators.volume_ratio)
            return volume_ratio is not None and volume_ratio <= self._config.volume_ratio_max
        if filter_name == "vwap_slope_strength":
            strength = self._vwap_slope_strength_atr(atr)
            return strength is not None and strength >= self._config.vwap_slope_min_atr
        if filter_name == "atr_pct_range":
            atr_pct = self._atr_pct(bar, atr)
            return (
                atr_pct is not None
                and self._config.atr_pct_min <= atr_pct <= self._config.atr_pct_max
            )
        if filter_name == "session_sigma_range":
            sigma_atr = self._session_sigma_atr(atr)
            return (
                sigma_atr is not None
                and self._config.session_sigma_min_atr
                <= sigma_atr
                <= self._config.session_sigma_max_atr
            )
        if filter_name == "rth_drive_min_atr":
            drive_atr = self._rth_drive_atr(atr)
            return drive_atr is not None and drive_atr >= self._config.rth_drive_min_atr
        if filter_name == "trend_regime_aligned":
            return (
                self._factor_filter_passes("vwap_slope_strength", bar, vwap, atr)
                and self._momentum_aligned(indicators.roc_120, Decimal("0"))
                and self._sma_pair_aligned(indicators.sma_fast, indicators.sma_slow)
            )
        if filter_name == "rth_drive_non_positive":
            return self._session.rth_drive is not None and direction * self._session.rth_drive <= 0
        if filter_name == "rth_drive_positive":
            return self._session.rth_drive is not None and direction * self._session.rth_drive > 0
        if filter_name == "rsi_mid":
            rsi = self._decimal(indicators.rsi)
            return rsi is not None and self._config.rsi_min <= rsi <= self._config.rsi_max
        if filter_name == "macd_aligned":
            macd_value = self._macd()
            return macd_value is not None and direction * macd_value.histogram > 0
        if filter_name == "adx_aligned":
            adx_value = self._adx()
            return (
                adx_value is not None
                and adx_value.adx >= self._config.adx_min
                and direction * (adx_value.plus_di - adx_value.minus_di) > 0
            )
        if filter_name == "cmf_positive":
            cmf = self._decimal(indicators.cmf)
            return cmf is not None and cmf > self._config.cmf_min
        if filter_name == "cmf_aligned":
            cmf = self._decimal(indicators.cmf)
            return cmf is not None and direction * cmf > self._config.cmf_min
        if filter_name == "mfi_mid":
            mfi = self._decimal(indicators.mfi)
            return mfi is not None and self._config.mfi_min <= mfi <= self._config.mfi_max
        if filter_name == "roc_aligned":
            roc = self._decimal(indicators.roc)
            return roc is not None and direction * roc >= self._config.roc_min_abs
        if filter_name == "mom60_aligned":
            return self._momentum_aligned(indicators.roc_60, Decimal("0"))
        if filter_name == "mom120_aligned":
            return self._momentum_aligned(indicators.roc_120, Decimal("0"))
        if filter_name == "mom240_aligned":
            return self._momentum_aligned(indicators.roc_240, Decimal("0"))
        if filter_name == "mom120_min":
            return self._momentum_aligned(indicators.roc_120, self._config.ts_momentum_min_abs)
        if filter_name == "ma20_80_aligned":
            return self._sma_pair_aligned(indicators.sma_fast, indicators.sma_slow)
        if filter_name == "ma50_200_aligned":
            return self._sma_pair_aligned(indicators.sma_long_fast, indicators.sma_long_slow)
        if filter_name == "technical_score_min":
            return self._technical_score(bar) >= self._config.technical_score_min
        if filter_name == "oscillator_score_min":
            return self._oscillator_score() >= self._config.oscillator_score_min
        if filter_name == "volume_curve_range":
            ratio = self._volume_curve_ratio(bar)
            return (
                ratio is not None
                and self._config.volume_curve_ratio_min
                <= ratio
                <= self._config.volume_curve_ratio_max
            )
        if filter_name == "cci_reversal":
            cci = self._decimal(indicators.cci)
            return cci is not None and direction * cci <= -self._config.cci_abs_min
        if filter_name == "stochastic_mid":
            stochastic_value = self._stochastic()
            return (
                stochastic_value is not None
                and self._config.stochastic_min
                <= stochastic_value.percent_k
                <= self._config.stochastic_max
            )
        if filter_name == "williams_mid":
            williams = self._decimal(indicators.williams_r)
            return (
                williams is not None
                and self._config.williams_r_min <= williams <= self._config.williams_r_max
            )
        if filter_name == "bollinger_inside":
            bollinger_value = self._bollinger()
            if bollinger_value is None or bollinger_value.standard_deviation == Decimal("0"):
                return False
            z_score = (bar.close - bollinger_value.middle) / bollinger_value.standard_deviation
            return abs(z_score) <= self._config.max_bollinger_z_abs
        if filter_name == "donchian_half_aligned":
            donchian_value = self._donchian()
            return (
                donchian_value is not None and direction * (bar.close - donchian_value.middle) > 0
            )
        if filter_name == "keltner_inside":
            keltner_value = self._keltner()
            return (
                keltner_value is not None
                and keltner_value.lower <= bar.close <= keltner_value.upper
            )
        raise ValueError(f"unknown research factor filter: {filter_name}")

    def _time_allowed(self, bar: Bar) -> bool:
        minute = self._et_minute(bar)
        window = self._config.time_window
        intervals = {
            "current_08_16": ((8 * 60, 16 * 60),),
            "evening_18_24": ((18 * 60, 24 * 60),),
            "evening_18_22": ((18 * 60, 22 * 60),),
            "overnight_18_06": ((18 * 60, 6 * 60),),
            "night_18_08": ((18 * 60, 8 * 60),),
            "asia_20_02": ((20 * 60, 2 * 60),),
            "early_00_08": ((0, 8 * 60),),
            "pre_rth_06_08": ((6 * 60, 8 * 60),),
            "rth_08_12": ((8 * 60, 12 * 60),),
            "rth_08_17": ((8 * 60, 17 * 60),),
            "day_08_14": ((8 * 60, 14 * 60),),
            "late_12_17": ((12 * 60, 17 * 60),),
            "bucket_08_16_full_anchor": ((8 * 60, 16 * 60),),
        }
        if window == "full_session":
            return not (17 * 60 <= minute < 18 * 60)
        if window == "avoid_06_08_14_17":
            return not (6 * 60 <= minute < 8 * 60 or 14 * 60 <= minute < 17 * 60)
        if window in intervals:
            return any(
                self._minute_in_interval(minute, start, end) for start, end in intervals[window]
            )
        raise ValueError(f"unknown time_window: {window}")

    @staticmethod
    def _minute_in_interval(minute: int, start: int, end: int) -> bool:
        if start < end:
            return start <= minute < end
        return minute >= start or minute < end

    def _update_session_state(self, bar: Bar) -> None:
        if bar.session_id != self._session.session_id:
            self._session = _SessionState(session_id=bar.session_id)
        vwap = self._decimal(self._require_indicators().vwap)
        if vwap is not None:
            deviation = bar.close - vwap
            self._session.sum_var_x_vol += deviation * deviation * bar.volume
            self._session.sum_vol += bar.volume
            history = self._session.vwap_history
            history.append(vwap)
            while len(history) > self._config.vwap_slope_lookback:
                history.popleft()
        self._update_rth_drive(bar)
        self._update_volume_curve(bar)

    def _update_rth_drive(self, bar: Bar) -> None:
        et = bar.end_time.astimezone(self._et_tz)
        minute = et.hour * 60 + et.minute
        if minute == 8 * 60:
            self._session.rth_open = bar.open
            self._session.rth_drive = None
        if minute == 9 * 60 and self._session.rth_open is not None:
            self._session.rth_drive = bar.close - self._session.rth_open

    def _update_volume_curve(self, bar: Bar) -> None:
        minute = self._et_minute(bar)
        history = self._volume_curve_history.setdefault(
            minute,
            deque(maxlen=self._config.volume_curve_lookback_sessions + 1),
        )
        history.append(bar.volume)

    def _vwap_slope_positive(self) -> bool | None:
        history = self._session.vwap_history
        if len(history) < self._config.vwap_slope_lookback:
            return None
        return history[-1] > history[0]

    def _session_sigma(self) -> Decimal | None:
        if self._session.sum_vol == Decimal("0"):
            return None
        variance = self._session.sum_var_x_vol / self._session.sum_vol
        if variance <= Decimal("0"):
            return Decimal("0")
        return variance.sqrt()

    def _long_rejection(self, bar: Bar, vwap: Decimal) -> bool:
        return bar.close > vwap and bar.close > bar.open and self._volume_confirmation()

    def _short_rejection(self, bar: Bar, vwap: Decimal) -> bool:
        return bar.close < vwap and bar.close < bar.open and self._volume_confirmation()

    def _volume_confirmation(self) -> bool:
        volume_ratio = self._decimal(self._require_indicators().volume_ratio)
        return volume_ratio is not None and volume_ratio >= self._config.min_volume_ratio

    def _near_session_close(self, bar: Bar) -> bool:
        et = bar.end_time.astimezone(self._et_tz)
        bar_minutes = et.hour * 60 + et.minute
        close_minutes = (
            self._config.session_close_et_hour * 60 + self._config.session_close_et_minute
        )
        return 0 <= close_minutes - bar_minutes <= self._config.minutes_before_close_flat

    def _exit(self, ctx: StrategyContext, reason: _ExitReason) -> None:
        if self._asset is not None:
            ctx.close(self._asset, metadata=self._exit_metadata(reason))
        self._reset()

    def _exit_metadata(self, reason: _ExitReason) -> dict[str, str]:
        payload = {"exit_reason": reason.value}
        if self._entry_price is not None:
            payload["entry_price"] = str(self._entry_price)
        if self._stop_price is not None:
            payload["stop_price"] = str(self._stop_price)
        if self._target_2 is not None:
            payload["target_price"] = str(self._target_2)
        return payload

    def _reset(self) -> None:
        self._state = _State.IDLE
        self._direction = None
        self._pullback_low = None
        self._pullback_high = None
        self._bars_in_wait = 0
        self._entry_price = None
        self._stop_price = None
        self._target_2 = None

    def _enter_state(self, state: _State, direction: _Direction) -> None:
        self._state = state
        self._direction = direction
        self._bars_in_wait = 0

    def _core_ready(self, indicators: _Indicators) -> bool:
        return indicators.vwap.ready and indicators.atr.ready and indicators.volume_ratio.ready

    def _require_indicators(self) -> _Indicators:
        if self._indicators is None:
            raise RuntimeError("strategy must be initialized before on_bar")
        return self._indicators

    def _direction_sign(self) -> Decimal:
        return Decimal("1") if self._direction is _Direction.LONG else Decimal("-1")

    def _momentum_aligned(self, indicator: AssetIndicator, minimum_abs: Decimal) -> bool:
        value = self._decimal(indicator)
        return value is not None and self._direction_sign() * value >= minimum_abs

    def _sma_pair_aligned(self, fast: AssetIndicator, slow: AssetIndicator) -> bool:
        fast_value = self._decimal(fast)
        slow_value = self._decimal(slow)
        return (
            fast_value is not None
            and slow_value is not None
            and self._direction_sign() * (fast_value - slow_value) > Decimal("0")
        )

    def _vwap_slope_strength_atr(self, atr: Decimal) -> Decimal | None:
        if atr <= Decimal("0"):
            return None
        history = self._session.vwap_history
        if len(history) < self._config.vwap_slope_lookback:
            return None
        return self._direction_sign() * (history[-1] - history[0]) / atr

    def _atr_pct(self, bar: Bar, atr: Decimal) -> Decimal | None:
        if atr <= Decimal("0") or bar.close <= Decimal("0"):
            return None
        return atr / bar.close

    def _session_sigma_atr(self, atr: Decimal) -> Decimal | None:
        if atr <= Decimal("0"):
            return None
        sigma = self._session_sigma()
        if sigma is None:
            return None
        return sigma / atr

    def _rth_drive_atr(self, atr: Decimal) -> Decimal | None:
        if atr <= Decimal("0") or self._session.rth_drive is None:
            return None
        return self._direction_sign() * self._session.rth_drive / atr

    def _technical_score(self, bar: Bar) -> int:
        indicators = self._require_indicators()
        direction = self._direction_sign()
        score = 0
        macd = self._macd()
        if macd is not None and direction * macd.histogram > Decimal("0"):
            score += 1
        adx = self._adx()
        if (
            adx is not None
            and adx.adx >= self._config.adx_min
            and direction * (adx.plus_di - adx.minus_di) > Decimal("0")
        ):
            score += 1
        roc = self._decimal(indicators.roc)
        if roc is not None and direction * roc > Decimal("0"):
            score += 1
        roc_60 = self._decimal(indicators.roc_60)
        if roc_60 is not None and direction * roc_60 > Decimal("0"):
            score += 1
        if self._sma_pair_aligned(indicators.sma_fast, indicators.sma_slow):
            score += 1
        donchian = self._donchian_long()
        if donchian is not None and direction * (bar.close - donchian.middle) > Decimal("0"):
            score += 1
        rsi = self._decimal(indicators.rsi)
        if rsi is not None and self._config.rsi_min <= rsi <= self._config.rsi_max:
            score += 1
        mfi = self._decimal(indicators.mfi)
        if mfi is not None and self._config.mfi_min <= mfi <= self._config.mfi_max:
            score += 1
        return score

    def _oscillator_score(self) -> int:
        indicators = self._require_indicators()
        score = 0
        rsi = self._decimal(indicators.rsi)
        if rsi is not None and self._config.rsi_min <= rsi <= self._config.rsi_max:
            score += 1
        mfi = self._decimal(indicators.mfi)
        if mfi is not None and self._config.mfi_min <= mfi <= self._config.mfi_max:
            score += 1
        stochastic = self._stochastic()
        if (
            stochastic is not None
            and self._config.stochastic_min <= stochastic.percent_k <= self._config.stochastic_max
        ):
            score += 1
        williams = self._decimal(indicators.williams_r)
        if (
            williams is not None
            and self._config.williams_r_min <= williams <= self._config.williams_r_max
        ):
            score += 1
        return score

    def _volume_curve_ratio(self, bar: Bar) -> Decimal | None:
        history = self._volume_curve_history.get(self._et_minute(bar))
        if history is None:
            return None
        observations = tuple(history)[:-1]
        if len(observations) < 5:
            return None
        average = sum(observations, Decimal("0")) / Decimal(len(observations))
        if average == Decimal("0"):
            return None
        return bar.volume / average

    def _et_minute(self, bar: Bar) -> int:
        et = bar.end_time.astimezone(self._et_tz)
        return et.hour * 60 + et.minute

    @staticmethod
    def _decimal(indicator: AssetIndicator) -> Decimal | None:
        value = indicator.value
        return value if isinstance(value, Decimal) else None

    def _adx(self) -> DirectionalMovementValue | None:
        value = self._require_indicators().adx.value
        return value if isinstance(value, DirectionalMovementValue) else None

    def _macd(self) -> MACDValue | None:
        value = self._require_indicators().macd.value
        return value if isinstance(value, MACDValue) else None

    def _bollinger(self) -> BollingerBandsValue | None:
        value = self._require_indicators().bollinger.value
        return value if isinstance(value, BollingerBandsValue) else None

    def _donchian(self) -> DonchianChannelValue | None:
        value = self._require_indicators().donchian.value
        return value if isinstance(value, DonchianChannelValue) else None

    def _donchian_long(self) -> DonchianChannelValue | None:
        value = self._require_indicators().donchian_long.value
        return value if isinstance(value, DonchianChannelValue) else None

    def _keltner(self) -> KeltnerChannelValue | None:
        value = self._require_indicators().keltner.value
        return value if isinstance(value, KeltnerChannelValue) else None

    def _stochastic(self) -> StochasticOscillatorValue | None:
        value = self._require_indicators().stochastic.value
        return value if isinstance(value, StochasticOscillatorValue) else None


__all__ = ["VwapFactorResearchConfig", "VwapFactorResearchStrategy"]
