"""Dual Supertrend trend-following strategy using the public Strategy SDK."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.strategy_sdk import (
    AssetIndicator,
    AssetRef,
    DirectionalMovementValue,
    Strategy,
    StrategyContext,
    SupertrendValue,
)


@dataclass(frozen=True, slots=True)
class DualSupertrendConfig:
    """Configuration for the single-asset dual Supertrend strategy."""

    symbol: str = "GC"
    timeframe: str = "1m"
    fast_window: int = 10
    fast_multiplier: Decimal = Decimal("2")
    slow_window: int = 20
    slow_multiplier: Decimal = Decimal("4")
    allow_short: bool = True
    base_target_percent: Decimal = Decimal("0.30")
    max_target_percent: Decimal = Decimal("0.50")
    use_adx_filter: bool = True
    adx_window: int = 14
    min_adx: Decimal = Decimal("20")
    use_volume_filter: bool = False
    volume_ratio_window: int = 20
    min_volume_ratio: Decimal = Decimal("1.0")
    use_atr_position_sizing: bool = True
    atr_window: int = 14
    target_atr_fraction: Decimal = Decimal("0.01")
    use_trading_hours_filter: bool = False
    trading_hours_timezone: str = "US/Eastern"
    trading_hours_start: str = "08:00"
    trading_hours_end: str = "16:00"
    stop_atr_multiple: Decimal = Decimal("0")
    trail_atr_multiple: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate configuration values."""
        for name in (
            "fast_window",
            "slow_window",
            "adx_window",
            "volume_ratio_window",
            "atr_window",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        for name in (
            "fast_multiplier",
            "slow_multiplier",
            "base_target_percent",
            "max_target_percent",
            "min_adx",
            "min_volume_ratio",
            "target_atr_fraction",
            "stop_atr_multiple",
            "trail_atr_multiple",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                object.__setattr__(self, name, Decimal(str(value)))
        if self.fast_multiplier < Decimal("0"):
            raise ValueError("fast_multiplier must be non-negative")
        if self.slow_multiplier < Decimal("0"):
            raise ValueError("slow_multiplier must be non-negative")
        if self.base_target_percent <= Decimal("0"):
            raise ValueError("base_target_percent must be positive")
        if self.max_target_percent <= Decimal("0"):
            raise ValueError("max_target_percent must be positive")
        if self.min_adx < Decimal("0"):
            raise ValueError("min_adx must be non-negative")
        if self.min_volume_ratio < Decimal("0"):
            raise ValueError("min_volume_ratio must be non-negative")
        if self.target_atr_fraction <= Decimal("0"):
            raise ValueError("target_atr_fraction must be positive")
        if self.stop_atr_multiple < Decimal("0"):
            raise ValueError("stop_atr_multiple must be non-negative")
        if self.trail_atr_multiple < Decimal("0"):
            raise ValueError("trail_atr_multiple must be non-negative")
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if not isinstance(self.allow_short, bool):
            raise ValueError("allow_short must be a bool")
        if not isinstance(self.use_adx_filter, bool):
            raise ValueError("use_adx_filter must be a bool")
        if not isinstance(self.use_volume_filter, bool):
            raise ValueError("use_volume_filter must be a bool")
        if not isinstance(self.use_atr_position_sizing, bool):
            raise ValueError("use_atr_position_sizing must be a bool")
        if not isinstance(self.use_trading_hours_filter, bool):
            raise ValueError("use_trading_hours_filter must be a bool")
        if self.use_trading_hours_filter:
            self._parse_time(self.trading_hours_start, "trading_hours_start")
            self._parse_time(self.trading_hours_end, "trading_hours_end")
            ZoneInfo(self.trading_hours_timezone)

    @staticmethod
    def _parse_time(value: str, name: str) -> time:
        """Parse HH:MM into a time value."""
        try:
            parts = value.split(":")
            if len(parts) != 2:
                raise ValueError
            hour = int(parts[0])
            minute = int(parts[1])
        except (AttributeError, ValueError) as exc:
            raise ValueError(f"{name} must use HH:MM") from exc
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"{name} must use HH:MM")
        return time(hour=hour, minute=minute)

    @property
    def trading_start_time(self) -> time:
        """Return the parsed start of the strategy trading window."""
        return self._parse_time(self.trading_hours_start, "trading_hours_start")

    @property
    def trading_end_time(self) -> time:
        """Return the parsed end of the strategy trading window."""
        return self._parse_time(self.trading_hours_end, "trading_hours_end")


@dataclass(frozen=True, slots=True)
class DualSupertrendIndicators:
    """Indicator bundle owned by the strategy lifecycle."""

    fast: AssetIndicator
    slow: AssetIndicator
    adx: AssetIndicator
    atr: AssetIndicator
    volume_ratio: AssetIndicator | None = None

    @property
    def ready(self) -> bool:
        """Return whether all configured indicators have values."""
        indicators = (self.fast, self.slow, self.adx, self.atr)
        if any(not indicator.ready or indicator.value is None for indicator in indicators):
            return False
        if self.volume_ratio is None:
            return True
        return self.volume_ratio.ready and self.volume_ratio.value is not None


class DualSupertrendStrategy(Strategy):
    """Dual Supertrend trend-following strategy with optional regime filters."""

    def __init__(self, config: DualSupertrendConfig | None = None) -> None:
        self._config = config or DualSupertrendConfig()
        self._asset: AssetRef | None = None
        self._indicators: DualSupertrendIndicators | None = None
        self._position_side: int = 0
        self._entry_price: Decimal | None = None
        self._stop_price: Decimal | None = None
        self._trailing_stop: Decimal | None = None
        self._tz: ZoneInfo | None = None
        self._trading_start: time | None = None
        self._trading_end: time | None = None
        if self._config.use_trading_hours_filter:
            self._tz = ZoneInfo(self._config.trading_hours_timezone)
            self._trading_start = self._config.trading_start_time
            self._trading_end = self._config.trading_end_time

    def initialize(self, ctx: StrategyContext) -> None:
        """Initialize subscriptions and indicators."""
        asset = ctx.symbol(self._config.symbol)
        self._asset = asset
        warmup = max(
            self._config.fast_window,
            self._config.slow_window,
            self._config.adx_window,
            self._config.atr_window,
            self._config.volume_ratio_window if self._config.use_volume_filter else 1,
        )
        ctx.subscribe(asset, timeframe=self._config.timeframe, warmup=warmup)
        volume_ratio = (
            ctx.indicator.volume_ratio(asset, self._config.volume_ratio_window)
            if self._config.use_volume_filter
            else None
        )
        self._indicators = DualSupertrendIndicators(
            fast=ctx.indicator.supertrend(
                asset,
                window=self._config.fast_window,
                multiplier=self._config.fast_multiplier,
            ),
            slow=ctx.indicator.supertrend(
                asset,
                window=self._config.slow_window,
                multiplier=self._config.slow_multiplier,
            ),
            adx=ctx.indicator.adx(asset, self._config.adx_window),
            atr=ctx.indicator.atr(asset, self._config.atr_window),
            volume_ratio=volume_ratio,
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        """Handle a completed strategy-facing bar."""
        if self._asset is None or self._indicators is None:
            raise RuntimeError("strategy must be initialized before on_bar")
        if bar.instrument_id != self._asset.instrument_id:
            return
        indicators = self._indicators
        if not indicators.ready:
            return

        fast = self._supertrend_value(indicators.fast)
        slow = self._supertrend_value(indicators.slow)
        atr = self._decimal_value(indicators.atr)
        if fast is None or slow is None or atr is None:
            return

        if self._close_on_software_risk(ctx, bar, atr):
            return
        if self._close_on_trend_flip(ctx, fast.direction):
            return
        if self._position_side != 0:
            return
        if not self.in_trading_hours(bar):
            return
        if not self._entry_filters_pass():
            return

        side = self._entry_side(fast.direction, slow.direction)
        if side == 0:
            return
        self._enter_position(ctx, bar, side, atr)

    def in_trading_hours(self, bar: Bar) -> bool:
        """Return whether a bar is inside the configured half-open time window."""
        if not self._config.use_trading_hours_filter:
            return True
        if self._tz is None or self._trading_start is None or self._trading_end is None:
            raise RuntimeError("trading hours filter was not initialized")
        local_time = bar.start_time.astimezone(self._tz).time()
        if self._trading_start <= self._trading_end:
            return self._trading_start <= local_time < self._trading_end
        return local_time >= self._trading_start or local_time < self._trading_end

    def _entry_filters_pass(self) -> bool:
        if self._indicators is None:
            return False
        if self._config.use_adx_filter:
            adx = self._adx_value(self._indicators.adx)
            if adx is None or adx < self._config.min_adx:
                return False
        if self._config.use_volume_filter:
            if self._indicators.volume_ratio is None:
                return False
            volume_ratio = self._decimal_value(self._indicators.volume_ratio)
            if volume_ratio is None or volume_ratio < self._config.min_volume_ratio:
                return False
        return True

    def _entry_side(self, fast_direction: int, slow_direction: int) -> int:
        if fast_direction == 1 and slow_direction == 1:
            return 1
        if fast_direction == -1 and slow_direction == -1 and self._config.allow_short:
            return -1
        return 0

    def _enter_position(self, ctx: StrategyContext, bar: Bar, side: int, atr: Decimal) -> None:
        if self._asset is None:
            return
        target = self._target_percent(bar.close, atr)
        if side < 0:
            target = -target
        self._position_side = side
        self._entry_price = bar.close
        self._stop_price = self._initial_stop(bar.close, atr, side)
        self._trailing_stop = None
        ctx.target_percent(self._asset, target)

    def _target_percent(self, close: Decimal, atr: Decimal) -> Decimal:
        target = self._config.base_target_percent
        if self._config.use_atr_position_sizing and atr > Decimal("0") and close > Decimal("0"):
            atr_fraction = atr / close
            target = self._config.base_target_percent * (
                self._config.target_atr_fraction / atr_fraction
            )
        return min(target, self._config.max_target_percent)

    def _initial_stop(self, close: Decimal, atr: Decimal, side: int) -> Decimal | None:
        if self._config.stop_atr_multiple <= Decimal("0") or atr <= Decimal("0"):
            return None
        if side > 0:
            return close - atr * self._config.stop_atr_multiple
        return close + atr * self._config.stop_atr_multiple

    def _close_on_trend_flip(self, ctx: StrategyContext, fast_direction: int) -> bool:
        if self._position_side > 0 and fast_direction == -1:
            self._close(ctx)
            return True
        if self._position_side < 0 and fast_direction == 1:
            self._close(ctx)
            return True
        return False

    def _close_on_software_risk(self, ctx: StrategyContext, bar: Bar, atr: Decimal) -> bool:
        if self._position_side == 0:
            return False
        if self._position_side > 0:
            stop = self._max_stop(self._stop_price, self._trailing_stop)
            if stop is not None and bar.low <= stop:
                self._close(ctx)
                return True
        else:
            stop = self._min_stop(self._stop_price, self._trailing_stop)
            if stop is not None and bar.high >= stop:
                self._close(ctx)
                return True
        self._update_trailing_stop(bar, atr)
        return False

    def _update_trailing_stop(self, bar: Bar, atr: Decimal) -> None:
        if self._config.trail_atr_multiple <= Decimal("0") or atr <= Decimal("0"):
            return
        offset = atr * self._config.trail_atr_multiple
        if self._position_side > 0:
            candidate = bar.close - offset
            self._trailing_stop = self._max_stop(self._trailing_stop, candidate)
        elif self._position_side < 0:
            candidate = bar.close + offset
            self._trailing_stop = self._min_stop(self._trailing_stop, candidate)

    def _close(self, ctx: StrategyContext) -> None:
        if self._asset is not None:
            ctx.close(self._asset)
        self._position_side = 0
        self._entry_price = None
        self._stop_price = None
        self._trailing_stop = None

    @staticmethod
    def _supertrend_value(indicator: AssetIndicator) -> SupertrendValue | None:
        value = indicator.value
        return value if isinstance(value, SupertrendValue) else None

    @staticmethod
    def _adx_value(indicator: AssetIndicator) -> Decimal | None:
        value = indicator.value
        if isinstance(value, DirectionalMovementValue):
            return value.adx
        return None

    @staticmethod
    def _decimal_value(indicator: AssetIndicator) -> Decimal | None:
        value = indicator.value
        return value if isinstance(value, Decimal) else None

    @staticmethod
    def _max_stop(left: Decimal | None, right: Decimal | None) -> Decimal | None:
        if left is None:
            return right
        if right is None:
            return left
        return max(left, right)

    @staticmethod
    def _min_stop(left: Decimal | None, right: Decimal | None) -> Decimal | None:
        if left is None:
            return right
        if right is None:
            return left
        return min(left, right)


__all__ = ["DualSupertrendConfig", "DualSupertrendIndicators", "DualSupertrendStrategy"]
