"""Production VWAP pullback strategies selected from VWAP research.

This module is the paper/live-facing implementation. It intentionally does not
depend on the research strategy/config classes and exposes only the stable GC
and SI variants selected from the research run.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.domain.positions import PositionSide
from qts.indicators.session_regime import TrailingSessionRegimeGate
from qts.strategy_sdk import AssetIndicator, AssetRef, Strategy, StrategyContext

_REGIME_RULES = frozenset({"off", "hard14", "hard_churn225", "hard14_ccvol17"})
_UNREADY_POLICIES = frozenset({"allow", "block"})
_CONFIRMATION_PROFILES = frozenset({"session_sigma_mom120", "trend_session_sigma"})


class _State(StrEnum):
    IDLE = "idle"
    WAIT_PULLBACK = "wait_pullback"
    WAIT_REJECTION = "wait_rejection"
    ENTERED = "entered"


class _ExitReason(StrEnum):
    SESSION_CLOSE_FLAT = "session_close_flat"
    LONG_CLOSE_BELOW_VWAP = "long_close_below_vwap"
    SHORT_CLOSE_ABOVE_VWAP = "short_close_above_vwap"
    LONG_STOP_ATR_TOUCHED = "long_stop_atr_touched"
    SHORT_STOP_ATR_TOUCHED = "short_stop_atr_touched"
    LONG_TARGET_R_TOUCHED = "long_target_r_touched"
    SHORT_TARGET_R_TOUCHED = "short_target_r_touched"


@dataclass(frozen=True, slots=True)
class VwapProductionRegimeGateConfig:
    """Trailing completed-session regime gate configuration."""

    rule: str = "hard_churn225"
    symbols: tuple[str, ...] = ("GC", "SI")
    timeframe: str = "15m"
    lookback_sessions: int = 120
    min_history_sessions: int = 120
    unready_policy: str = "block"
    asia_start_et_hour: int = 20
    asia_end_et_hour: int = 2
    range_min: Decimal = Decimal("0.015")
    asia_share_max: Decimal = Decimal("0.14")
    min_return_floor: Decimal = Decimal("-0.15")
    mean_churn_min: Decimal = Decimal("2.25")
    mean_realized_vol_max: Decimal = Decimal("0.017")

    def __post_init__(self) -> None:
        rule = str(self.rule).strip().lower()
        if rule not in _REGIME_RULES:
            raise ValueError(f"rule must be one of {sorted(_REGIME_RULES)}")
        object.__setattr__(self, "rule", rule)
        unready_policy = str(self.unready_policy).strip().lower()
        if unready_policy not in _UNREADY_POLICIES:
            raise ValueError(f"unready_policy must be one of {sorted(_UNREADY_POLICIES)}")
        object.__setattr__(self, "unready_policy", unready_policy)
        symbols = (self.symbols,) if isinstance(self.symbols, str) else tuple(self.symbols)
        symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if rule != "off" and not symbols:
            raise ValueError("symbols must be non-empty when regime gate is enabled")
        if any(not symbol for symbol in symbols):
            raise ValueError("symbols must not contain empty values")
        object.__setattr__(self, "symbols", symbols)
        if self.lookback_sessions <= 0:
            raise ValueError("lookback_sessions must be positive")
        if self.min_history_sessions <= 0:
            raise ValueError("min_history_sessions must be positive")
        if self.min_history_sessions > self.lookback_sessions:
            raise ValueError("min_history_sessions must be <= lookback_sessions")
        if not self.timeframe.strip():
            raise ValueError("timeframe must be non-empty")
        for name in (
            "range_min",
            "asia_share_max",
            "min_return_floor",
            "mean_churn_min",
            "mean_realized_vol_max",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                object.__setattr__(self, name, Decimal(str(value)))
        if self.range_min <= Decimal("0"):
            raise ValueError("range_min must be positive")
        if not Decimal("0") <= self.asia_share_max <= Decimal("1"):
            raise ValueError("asia_share_max must be between 0 and 1")
        if self.mean_churn_min <= Decimal("0"):
            raise ValueError("mean_churn_min must be positive")
        if self.mean_realized_vol_max <= Decimal("0"):
            raise ValueError("mean_realized_vol_max must be positive")
        if not (0 <= self.asia_start_et_hour < 24):
            raise ValueError("asia_start_et_hour must be 0..23")
        if not (0 <= self.asia_end_et_hour <= 24):
            raise ValueError("asia_end_et_hour must be 0..24")
        if self.asia_start_et_hour == self.asia_end_et_hour:
            raise ValueError("asia_start_et_hour must differ from asia_end_et_hour")


@dataclass(frozen=True, slots=True)
class VwapProductionPullbackConfig:
    """Small paper/live configuration for the stable production strategy."""

    symbol: str = "GC"
    timeframe: str = "15m"
    target_quantity: Decimal = Decimal("4")
    min_volume_ratio: Decimal = Decimal("1.3")
    confirmation_profile: str = "session_sigma_mom120"

    atr_window: int = 14
    volume_ratio_window: int = 20
    vwap_slope_lookback: int = 5
    max_bars_in_wait_state: int = 5
    pullback_touch_atr_below: Decimal = Decimal("0.15")
    pullback_touch_atr_above: Decimal = Decimal("0.1")
    max_pullback_break_atr: Decimal = Decimal("1.0")
    stop_atr_multiple: Decimal = Decimal("1.0")
    target_r_multiple: Decimal = Decimal("2.0")
    exit_on_vwap_cross: bool = False
    session_sigma_min_atr: Decimal = Decimal("0.05")
    session_sigma_max_atr: Decimal = Decimal("2.00")
    vwap_slope_min_atr: Decimal = Decimal("0.10")
    regime_gate: Any = field(default_factory=VwapProductionRegimeGateConfig)

    entry_window: str = field(default="asia_20_02", init=False)
    ts_momentum_120_window: int = field(default=120, init=False)
    sma_fast_window: int = field(default=20, init=False)
    sma_slow_window: int = field(default=80, init=False)
    min_session_open_minutes: int = field(default=0, init=False)
    session_open_et_hour: int = field(default=18, init=False)
    session_open_et_minute: int = field(default=0, init=False)
    minutes_before_close_flat: int = field(default=30, init=False)
    session_close_et_hour: int = field(default=17, init=False)
    session_close_et_minute: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        timeframe = str(self.timeframe).strip().lower()
        if not timeframe:
            raise ValueError("timeframe is required")
        object.__setattr__(self, "timeframe", timeframe)
        profile = str(self.confirmation_profile).strip().lower()
        if profile not in _CONFIRMATION_PROFILES:
            raise ValueError(
                f"confirmation_profile must be one of {sorted(_CONFIRMATION_PROFILES)}"
            )
        object.__setattr__(self, "confirmation_profile", profile)
        if isinstance(self.exit_on_vwap_cross, str):
            object.__setattr__(
                self,
                "exit_on_vwap_cross",
                self.exit_on_vwap_cross.strip().lower() in {"1", "true", "yes", "on"},
            )
        for name in (
            "target_quantity",
            "min_volume_ratio",
            "pullback_touch_atr_below",
            "pullback_touch_atr_above",
            "max_pullback_break_atr",
            "stop_atr_multiple",
            "target_r_multiple",
            "session_sigma_min_atr",
            "session_sigma_max_atr",
            "vwap_slope_min_atr",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                object.__setattr__(self, name, Decimal(str(value)))
        if self.target_quantity <= Decimal("0"):
            raise ValueError("target_quantity must be positive")
        if self.min_volume_ratio <= Decimal("0"):
            raise ValueError("min_volume_ratio must be positive")
        if self.pullback_touch_atr_below <= Decimal("0"):
            raise ValueError("pullback_touch_atr_below must be positive")
        if self.max_pullback_break_atr <= Decimal("0"):
            raise ValueError("max_pullback_break_atr must be positive")
        if self.stop_atr_multiple <= Decimal("0"):
            raise ValueError("stop_atr_multiple must be positive")
        if self.target_r_multiple <= Decimal("0"):
            raise ValueError("target_r_multiple must be positive")
        if self.session_sigma_min_atr > self.session_sigma_max_atr:
            raise ValueError("session_sigma_min_atr must be <= session_sigma_max_atr")
        for name in (
            "atr_window",
            "volume_ratio_window",
            "vwap_slope_lookback",
            "max_bars_in_wait_state",
            "ts_momentum_120_window",
            "sma_fast_window",
            "sma_slow_window",
            "minutes_before_close_flat",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.sma_fast_window >= self.sma_slow_window:
            raise ValueError("sma_fast_window must be < sma_slow_window")
        if not isinstance(self.regime_gate, VwapProductionRegimeGateConfig):
            object.__setattr__(
                self,
                "regime_gate",
                VwapProductionRegimeGateConfig(**self.regime_gate),
            )
        if self.regime_gate.timeframe.strip().lower() != self.timeframe:
            object.__setattr__(
                self,
                "regime_gate",
                replace(self.regime_gate, timeframe=self.timeframe),
            )

    @property
    def required_warmup_bars(self) -> int:
        """Return the main strategy warmup required by configured indicators."""
        return max(
            self.atr_window,
            self.volume_ratio_window,
            self.vwap_slope_lookback,
            self.ts_momentum_120_window,
            self.sma_fast_window,
            self.sma_slow_window,
        )

    @classmethod
    def gc_best_stable(cls) -> VwapProductionPullbackConfig:
        """Return the selected GC production candidate."""
        return cls(
            symbol="GC",
            timeframe="15m",
            target_quantity=Decimal("4"),
            min_volume_ratio=Decimal("1.3"),
            confirmation_profile="session_sigma_mom120",
            regime_gate=VwapProductionRegimeGateConfig(rule="hard_churn225"),
        )

    @classmethod
    def si_best_stable(cls) -> VwapProductionPullbackConfig:
        """Return the selected SI production candidate."""
        return cls(
            symbol="SI",
            timeframe="15m",
            target_quantity=Decimal("3"),
            min_volume_ratio=Decimal("1.5"),
            confirmation_profile="trend_session_sigma",
            regime_gate=VwapProductionRegimeGateConfig(rule="hard14_ccvol17"),
        )


@dataclass(slots=True)
class _SessionState:
    session_id: str | None = None
    sum_var_x_vol: Decimal = Decimal("0")
    sum_vol: Decimal = Decimal("0")
    vwap_history: deque[Decimal] = field(default_factory=deque)


@dataclass(slots=True)
class _ProductionIndicators:
    vwap: AssetIndicator
    atr: AssetIndicator
    volume_ratio: AssetIndicator
    roc_120: AssetIndicator
    sma_fast: AssetIndicator
    sma_slow: AssetIndicator


_TrailingRegimeGate = TrailingSessionRegimeGate


class VwapProductionPullbackStrategy(Strategy):
    """Production VWAP pullback strategy with online regime gating."""

    def __init__(
        self,
        config: VwapProductionPullbackConfig | None = None,
        **overrides: Any,
    ) -> None:
        if config is not None and overrides:
            raise ValueError("pass either config or overrides, not both")
        self._config = config if config is not None else VwapProductionPullbackConfig(**overrides)
        self._regime_config: VwapProductionRegimeGateConfig = self._config.regime_gate
        self._regime_gate = _TrailingRegimeGate(self._regime_config)
        self._regime_symbol_by_instrument_id: dict[object, str] = {}
        self._asset: AssetRef | None = None
        self._indicators: _ProductionIndicators | None = None
        self._state: _State = _State.IDLE
        self._direction: PositionSide | None = None
        self._pullback_low: Decimal | None = None
        self._pullback_high: Decimal | None = None
        self._bars_in_wait = 0
        self._entry_price: Decimal | None = None
        self._stop_price: Decimal | None = None
        self._target_2: Decimal | None = None
        self._session = _SessionState()
        self._et_tz = ZoneInfo("US/Eastern")
        self._confirmation_diagnostics: tuple[dict[str, object], ...] = ()

    @property
    def confirmation_diagnostics(self) -> tuple[dict[str, object], ...]:
        """Return production confirmation observations from the last entry check."""
        return self._confirmation_diagnostics

    def initialize(self, ctx: StrategyContext) -> None:
        asset = ctx.symbol(self._config.symbol)
        self._asset = asset
        subscription_warmups = {
            asset.instrument_id: (asset, self._config.required_warmup_bars),
        }
        self._indicators = _ProductionIndicators(
            vwap=ctx.indicator.session_vwap(asset),
            atr=ctx.indicator.atr(asset, self._config.atr_window),
            volume_ratio=ctx.indicator.volume_ratio(asset, self._config.volume_ratio_window),
            roc_120=ctx.indicator.rate_of_change(asset, self._config.ts_momentum_120_window),
            sma_fast=ctx.indicator.sma(asset, self._config.sma_fast_window),
            sma_slow=ctx.indicator.sma(asset, self._config.sma_slow_window),
        )
        if self._regime_config.rule != "off":
            regime_warmup = _regime_warmup_bars(
                self._regime_config,
                timeframe=self._config.timeframe,
            )
            for symbol in self._regime_config.symbols:
                regime_asset = ctx.symbol(symbol)
                self._regime_symbol_by_instrument_id[regime_asset.instrument_id] = symbol
                current = subscription_warmups.get(regime_asset.instrument_id)
                if current is None:
                    subscription_warmups[regime_asset.instrument_id] = (
                        regime_asset,
                        regime_warmup,
                    )
                else:
                    subscription_warmups[regime_asset.instrument_id] = (
                        current[0],
                        max(current[1], regime_warmup),
                    )
        for subscribed_asset, warmup in subscription_warmups.values():
            ctx.subscribe(subscribed_asset, timeframe=self._config.timeframe, warmup=warmup)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        regime_symbol = self._regime_symbol_by_instrument_id.get(bar.instrument_id)
        if regime_symbol is not None:
            self._regime_gate.update_bar(regime_symbol, bar)
        if self._asset is not None and bar.instrument_id != self._asset.instrument_id:
            return
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
        if self._state is not _State.ENTERED and not self._regime_gate.allows_new_entries():
            self._reset()
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
            self._enter_state(_State.WAIT_PULLBACK, PositionSide.LONG)
        elif slope_up is False and bar.close < vwap:
            self._enter_state(_State.WAIT_PULLBACK, PositionSide.SHORT)

    def _step_wait_pullback(self, bar: Bar, vwap: Decimal, atr: Decimal) -> None:
        self._bars_in_wait += 1
        if self._bars_in_wait > self._config.max_bars_in_wait_state:
            self._reset()
            return
        if not self._time_allowed(bar):
            self._reset()
            return
        if self._direction is PositionSide.LONG:
            if bar.close < vwap - atr * self._config.max_pullback_break_atr:
                self._reset()
                return
            if (
                vwap - atr * self._config.pullback_touch_atr_below
                <= bar.low
                <= vwap + atr * self._config.pullback_touch_atr_above
            ):
                self._pullback_low = bar.low
                self._enter_state(_State.WAIT_REJECTION, PositionSide.LONG)
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
                self._enter_state(_State.WAIT_REJECTION, PositionSide.SHORT)

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
        if self._direction is PositionSide.LONG:
            self._pullback_low = min(self._pullback_low or bar.low, bar.low)
            if bar.close < vwap - atr * self._config.max_pullback_break_atr:
                self._reset()
                return
            if self._long_rejection(bar, vwap) and self._confirmations_pass(bar, vwap, atr):
                self._enter_position(ctx, bar, atr)
        else:
            self._pullback_high = max(self._pullback_high or bar.high, bar.high)
            if bar.close > vwap + atr * self._config.max_pullback_break_atr:
                self._reset()
                return
            if self._short_rejection(bar, vwap) and self._confirmations_pass(bar, vwap, atr):
                self._enter_position(ctx, bar, atr)

    def _step_entered(self, ctx: StrategyContext, bar: Bar, vwap: Decimal) -> None:
        if self._direction is PositionSide.LONG:
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

    def _enter_position(self, ctx: StrategyContext, bar: Bar, atr: Decimal) -> None:
        if self._asset is None:
            return
        self._entry_price = bar.close
        stop_distance = atr * self._config.stop_atr_multiple
        target_distance = stop_distance * self._config.target_r_multiple
        metadata = self._entry_metadata()
        if self._direction is PositionSide.LONG:
            self._stop_price = self._entry_price - stop_distance
            self._target_2 = self._entry_price + target_distance
            ctx.target_quantity(self._asset, self._config.target_quantity, metadata=metadata)
        else:
            self._stop_price = self._entry_price + stop_distance
            self._target_2 = self._entry_price - target_distance
            ctx.target_quantity(self._asset, -self._config.target_quantity, metadata=metadata)
        self._state = _State.ENTERED
        self._bars_in_wait = 0

    def _entry_metadata(self) -> dict[str, str] | None:
        if not self._confirmation_diagnostics:
            return None
        return {
            "confirmation_diagnostics": json.dumps(
                list(self._confirmation_diagnostics),
                separators=(",", ":"),
                sort_keys=True,
            )
        }

    def _confirmations_pass(self, bar: Bar, vwap: Decimal, atr: Decimal) -> bool:
        if self._config.confirmation_profile == "session_sigma_mom120":
            confirmations = ("session_sigma_range", "mom120_aligned")
        elif self._config.confirmation_profile == "trend_session_sigma":
            confirmations = ("trend_regime_aligned", "session_sigma_range")
        else:
            raise ValueError(f"unknown confirmation_profile: {self._config.confirmation_profile}")

        diagnostics: list[dict[str, object]] = []
        for name in confirmations:
            passed = self._confirmation_passes(name, bar, vwap, atr)
            diagnostics.append(
                {
                    "confirmation": name,
                    "passed": passed,
                    "value": self._confirmation_value(name, bar, vwap, atr),
                }
            )
            self._confirmation_diagnostics = tuple(diagnostics)
            if not passed:
                return False
        self._confirmation_diagnostics = tuple(diagnostics)
        return True

    def _confirmation_passes(
        self,
        name: str,
        bar: Bar,
        vwap: Decimal,
        atr: Decimal,
    ) -> bool:
        _ = bar, vwap
        indicators = self._require_indicators()
        if name == "session_sigma_range":
            sigma_atr = self._session_sigma_atr(atr)
            return (
                sigma_atr is not None
                and self._config.session_sigma_min_atr
                <= sigma_atr
                <= self._config.session_sigma_max_atr
            )
        if name == "mom120_aligned":
            return self._momentum_aligned(indicators.roc_120, Decimal("0"))
        if name == "trend_regime_aligned":
            slope_strength = self._vwap_slope_strength_atr(atr)
            return (
                slope_strength is not None
                and slope_strength >= self._config.vwap_slope_min_atr
                and self._momentum_aligned(indicators.roc_120, Decimal("0"))
                and self._sma_pair_aligned(indicators.sma_fast, indicators.sma_slow)
            )
        raise ValueError(f"unknown production confirmation: {name}")

    def _confirmation_value(
        self,
        name: str,
        bar: Bar,
        vwap: Decimal,
        atr: Decimal,
    ) -> str | None:
        _ = bar, vwap
        indicators = self._require_indicators()
        if name == "session_sigma_range":
            return self._format_decimal(self._session_sigma_atr(atr))
        if name == "mom120_aligned":
            return self._format_decimal(self._decimal(indicators.roc_120))
        if name == "trend_regime_aligned":
            strength = self._format_decimal(self._vwap_slope_strength_atr(atr))
            momentum = self._format_decimal(self._decimal(indicators.roc_120))
            ma_spread = self._sma_spread(indicators.sma_fast, indicators.sma_slow)
            return f"vwap_slope_atr={strength},roc120={momentum},ma20_80={ma_spread}"
        return None

    def _time_allowed(self, bar: Bar) -> bool:
        minute = self._et_minute(bar)
        allowed = self._minute_in_interval(minute, 20 * 60, 2 * 60)
        return allowed and self._session_open_cooloff_elapsed(bar)

    @staticmethod
    def _minute_in_interval(minute: int, start: int, end: int) -> bool:
        if start < end:
            return start <= minute < end
        return minute >= start or minute < end

    def _session_open_cooloff_elapsed(self, bar: Bar) -> bool:
        return self._minutes_since_session_open(bar) >= self._config.min_session_open_minutes

    def _minutes_since_session_open(self, bar: Bar) -> int:
        minute = self._et_minute(bar)
        open_minute = self._config.session_open_et_hour * 60 + self._config.session_open_et_minute
        if minute >= open_minute:
            return minute - open_minute
        return minute + 24 * 60 - open_minute

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

    def _enter_state(self, state: _State, direction: PositionSide) -> None:
        self._state = state
        self._direction = direction
        self._bars_in_wait = 0

    def _core_ready(self, indicators: _ProductionIndicators) -> bool:
        return indicators.vwap.ready and indicators.atr.ready and indicators.volume_ratio.ready

    def _require_indicators(self) -> _ProductionIndicators:
        if self._indicators is None:
            raise RuntimeError("strategy must be initialized before on_bar")
        return self._indicators

    def _direction_sign(self) -> Decimal:
        return Decimal("1") if self._direction is PositionSide.LONG else Decimal("-1")

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

    def _sma_spread(self, fast: AssetIndicator, slow: AssetIndicator) -> str | None:
        fast_value = self._decimal(fast)
        slow_value = self._decimal(slow)
        if fast_value is None or slow_value is None:
            return None
        return self._format_decimal(fast_value - slow_value)

    def _vwap_slope_strength_atr(self, atr: Decimal) -> Decimal | None:
        if atr <= Decimal("0"):
            return None
        history = self._session.vwap_history
        if len(history) < self._config.vwap_slope_lookback:
            return None
        return self._direction_sign() * (history[-1] - history[0]) / atr

    def _session_sigma_atr(self, atr: Decimal) -> Decimal | None:
        if atr <= Decimal("0"):
            return None
        sigma = self._session_sigma()
        if sigma is None:
            return None
        return sigma / atr

    def _et_minute(self, bar: Bar) -> int:
        et = bar.end_time.astimezone(self._et_tz)
        return et.hour * 60 + et.minute

    @staticmethod
    def _decimal(indicator: AssetIndicator) -> Decimal | None:
        value = indicator.value
        return value if isinstance(value, Decimal) else None

    @staticmethod
    def _format_decimal(value: Decimal | None) -> str | None:
        if value is None:
            return None
        return str(value.normalize())


class GcVwapProductionPullbackStrategy(VwapProductionPullbackStrategy):
    """GC production variant selected for stability across failure windows."""

    def __init__(
        self,
        config: VwapProductionPullbackConfig | None = None,
        **overrides: Any,
    ) -> None:
        base = config if config is not None else VwapProductionPullbackConfig.gc_best_stable()
        if config is not None and overrides:
            raise ValueError("pass either config or overrides, not both")
        super().__init__(replace(base, **overrides) if overrides else base)


class SiVwapProductionPullbackStrategy(VwapProductionPullbackStrategy):
    """SI production variant selected for return while controlling failure windows."""

    def __init__(
        self,
        config: VwapProductionPullbackConfig | None = None,
        **overrides: Any,
    ) -> None:
        base = config if config is not None else VwapProductionPullbackConfig.si_best_stable()
        if config is not None and overrides:
            raise ValueError("pass either config or overrides, not both")
        super().__init__(replace(base, **overrides) if overrides else base)


def _regime_warmup_bars(
    config: VwapProductionRegimeGateConfig,
    *,
    timeframe: str | None = None,
) -> int:
    timeframe = (timeframe or config.timeframe).strip().lower()
    if not timeframe.endswith("m"):
        return config.lookback_sessions + 2
    minutes = int(timeframe[:-1])
    if minutes <= 0:
        raise ValueError("minute timeframe must be positive")
    bars_per_full_session = (23 * 60 + minutes - 1) // minutes
    return config.lookback_sessions * bars_per_full_session + 2


__all__ = [
    "GcVwapProductionPullbackStrategy",
    "SiVwapProductionPullbackStrategy",
    "VwapProductionPullbackConfig",
    "VwapProductionPullbackStrategy",
    "VwapProductionRegimeGateConfig",
]
