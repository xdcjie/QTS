"""VWAP pullback strategy example using only the public Strategy SDK."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, TypedDict, Unpack

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetIndicator, AssetRef, Strategy, StrategyContext

Direction = Literal["LONG", "SHORT"]


class VwapPullbackConfigOverrides(TypedDict, total=False):
    """Typed constructor overrides for the VWAP pullback example."""

    symbol: str
    timeframe: str
    ma_20_window: int
    ma_26_window: int
    ma_32_window: int
    atr_window: int
    rsi_window: int
    volume_ratio_window: int
    opening_range_bars: int
    target_quantity: Decimal
    max_pullback_atr: Decimal
    key_level_atr: Decimal
    min_rsi: Decimal
    max_rsi: Decimal
    short_min_rsi: Decimal
    short_max_rsi: Decimal
    min_volume_ratio: Decimal
    entry_threshold: int
    l1_min: int
    l2_min: int
    l3_min: int
    stop_atr_multiple: Decimal
    take_profit_atr_multiple: Decimal
    trailing_atr_multiple: Decimal


@dataclass(frozen=True, slots=True)
class VwapPullbackConfig:
    """Configuration for the VWAP pullback example strategy."""

    symbol: str = "AAPL"
    timeframe: str = "1m"
    ma_20_window: int = 20
    ma_26_window: int = 26
    ma_32_window: int = 32
    atr_window: int = 7
    rsi_window: int = 14
    volume_ratio_window: int = 20
    opening_range_bars: int = 5
    target_quantity: Decimal = Decimal("1")
    max_pullback_atr: Decimal = Decimal("0.75")
    key_level_atr: Decimal = Decimal("0.50")
    min_rsi: Decimal = Decimal("45")
    max_rsi: Decimal = Decimal("70")
    short_min_rsi: Decimal = Decimal("30")
    short_max_rsi: Decimal = Decimal("55")
    min_volume_ratio: Decimal = Decimal("1.2")
    entry_threshold: int = 60
    l1_min: int = 6
    l2_min: int = 10
    l3_min: int = 10
    stop_atr_multiple: Decimal = Decimal("1.2")
    take_profit_atr_multiple: Decimal = Decimal("2.0")
    trailing_atr_multiple: Decimal = Decimal("1.0")

    def __post_init__(self) -> None:
        # Coerce YAML-deserialized strings into proper Decimals before validation.
        for decimal_field in (
            "target_quantity",
            "max_pullback_atr",
            "key_level_atr",
            "min_rsi",
            "max_rsi",
            "short_min_rsi",
            "short_max_rsi",
            "min_volume_ratio",
            "stop_atr_multiple",
            "take_profit_atr_multiple",
            "trailing_atr_multiple",
        ):
            current = getattr(self, decimal_field)
            if not isinstance(current, Decimal):
                object.__setattr__(self, decimal_field, Decimal(str(current)))
        positive_ints = {
            "ma_20_window": self.ma_20_window,
            "ma_26_window": self.ma_26_window,
            "ma_32_window": self.ma_32_window,
            "atr_window": self.atr_window,
            "rsi_window": self.rsi_window,
            "volume_ratio_window": self.volume_ratio_window,
            "opening_range_bars": self.opening_range_bars,
            "entry_threshold": self.entry_threshold,
        }
        for int_name, int_value in positive_ints.items():
            if int_value <= 0:
                raise ValueError(f"{int_name} must be positive")
        positive_decimals = {
            "target_quantity": self.target_quantity,
            "max_pullback_atr": self.max_pullback_atr,
            "key_level_atr": self.key_level_atr,
            "min_volume_ratio": self.min_volume_ratio,
            "stop_atr_multiple": self.stop_atr_multiple,
            "take_profit_atr_multiple": self.take_profit_atr_multiple,
            "trailing_atr_multiple": self.trailing_atr_multiple,
        }
        for decimal_name, decimal_value in positive_decimals.items():
            if decimal_value <= 0:
                raise ValueError(f"{decimal_name} must be positive")
        if self.min_rsi > self.max_rsi:
            raise ValueError("min_rsi must be less than or equal to max_rsi")
        if self.short_min_rsi > self.short_max_rsi:
            raise ValueError("short_min_rsi must be less than or equal to short_max_rsi")


@dataclass(frozen=True, slots=True)
class VwapPullbackScore:
    """Layered VWAP pullback score for one direction."""

    direction: Direction
    l1: int
    l2: int
    l3: int
    details: tuple[str, ...] = ()

    @property
    def total(self) -> int:
        """Return the summed L1/L2/L3 score."""
        return self.l1 + self.l2 + self.l3


@dataclass(frozen=True, slots=True)
class VwapPullbackIndicators:
    """Initialized indicator set for the VWAP pullback strategy."""

    MA_20: AssetIndicator
    MA_26: AssetIndicator
    MA_32: AssetIndicator
    ATR_7: AssetIndicator
    RSI_14: AssetIndicator
    VWAP: AssetIndicator
    volume_ratio: AssetIndicator

    @property
    def ready(self) -> bool:
        """Return whether every indicator has a usable value."""
        return all(
            indicator.ready and indicator.value is not None
            for indicator in (
                self.MA_20,
                self.MA_26,
                self.MA_32,
                self.ATR_7,
                self.RSI_14,
                self.VWAP,
                self.volume_ratio,
            )
        )


class VwapPullbackStrategy(Strategy):
    """Bar-level VWAP pullback strategy with SDK-managed indicators."""

    def __init__(
        self,
        config: VwapPullbackConfig | None = None,
        **overrides: Unpack[VwapPullbackConfigOverrides],
    ) -> None:
        if config is not None and overrides:
            raise ValueError("pass either config or constructor overrides, not both")
        if config is None:
            config = VwapPullbackConfig(**overrides)
        self._config = config
        self._asset: AssetRef | None = None
        self._indicators: VwapPullbackIndicators | None = None
        self._session_id: str | None = None
        self._bars_in_session = 0
        self._opening_range_high: Decimal | None = None
        self._opening_range_low: Decimal | None = None
        self._current_session_high: Decimal | None = None
        self._current_session_low: Decimal | None = None
        self._prior_session_high: Decimal | None = None
        self._prior_session_low: Decimal | None = None
        self._position_direction: Direction | None = None
        self._entry_price: Decimal | None = None
        self._stop: Decimal | None = None
        self._take_profit: Decimal | None = None
        self._trailing_stop: Decimal | None = None
        self._last_score: VwapPullbackScore | None = None

    @property
    def config(self) -> VwapPullbackConfig:
        """Return the immutable strategy configuration."""
        return self._config

    @property
    def last_score(self) -> VwapPullbackScore | None:
        """Return the most recent accepted entry score."""
        return self._last_score

    def initialize(self, ctx: StrategyContext) -> None:
        asset = ctx.symbol(self._config.symbol)
        self._asset = asset
        self._indicators = VwapPullbackIndicators(
            MA_20=ctx.indicator.ema(asset, self._config.ma_20_window),
            MA_26=ctx.indicator.ema(asset, self._config.ma_26_window),
            MA_32=ctx.indicator.ema(asset, self._config.ma_32_window),
            ATR_7=ctx.indicator.atr(asset, self._config.atr_window),
            RSI_14=ctx.indicator.rsi(asset, self._config.rsi_window),
            VWAP=ctx.indicator.session_vwap(asset),
            volume_ratio=ctx.indicator.volume_ratio(asset, self._config.volume_ratio_window),
        )
        ctx.subscribe(
            asset,
            timeframe=self._config.timeframe,
            warmup=max(
                self._config.ma_20_window,
                self._config.ma_26_window,
                self._config.ma_32_window,
                self._config.atr_window,
                self._config.rsi_window,
                self._config.volume_ratio_window,
            ),
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._asset is None:
            raise RuntimeError("strategy must be initialized before on_bar")

        self._record_session_bar(bar)
        self._manage_exit(ctx, bar)
        if self._position_direction is not None:
            return
        if self._bars_in_session <= self._config.opening_range_bars:
            return
        if not self._indicators_ready():
            return
        score = self._best_entry_score(bar)
        if score is None:
            return
        self._enter(ctx, bar, score)

    def _record_session_bar(self, bar: Bar) -> None:
        session_id = str(bar.session_id)
        if session_id != self._session_id:
            self._prior_session_high = self._current_session_high
            self._prior_session_low = self._current_session_low
            self._session_id = session_id
            self._bars_in_session = 0
            self._opening_range_high = None
            self._opening_range_low = None
            self._current_session_high = None
            self._current_session_low = None

        self._bars_in_session += 1
        self._current_session_high = self._max_decimal(self._current_session_high, bar.high)
        self._current_session_low = self._min_decimal(self._current_session_low, bar.low)
        if self._bars_in_session <= self._config.opening_range_bars:
            self._opening_range_high = self._max_decimal(self._opening_range_high, bar.high)
            self._opening_range_low = self._min_decimal(self._opening_range_low, bar.low)

    def _manage_exit(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._position_direction is None or self._entry_price is None:
            return
        ATR_7 = self._required_indicator_value(self._require_indicators().ATR_7, "ATR_7")

        if self._position_direction == "LONG":
            trailing_candidate = bar.high - (ATR_7 * self._config.trailing_atr_multiple)
            self._trailing_stop = self._max_decimal(self._trailing_stop, trailing_candidate)
            effective_stop = self._max_decimal(self._stop, self._trailing_stop)
            hit_stop = effective_stop is not None and bar.low <= effective_stop
            hit_target = self._take_profit is not None and bar.high >= self._take_profit
        else:
            trailing_candidate = bar.low + (ATR_7 * self._config.trailing_atr_multiple)
            self._trailing_stop = self._min_decimal(self._trailing_stop, trailing_candidate)
            effective_stop = self._min_decimal(self._stop, self._trailing_stop)
            hit_stop = effective_stop is not None and bar.high >= effective_stop
            hit_target = self._take_profit is not None and bar.low <= self._take_profit

        if hit_stop or hit_target:
            ctx.close(self._require_asset())
            self._clear_position()

    def _indicators_ready(self) -> bool:
        return self._require_indicators().ready

    def _best_entry_score(self, bar: Bar) -> VwapPullbackScore | None:
        candidates = (
            self._score_direction("LONG", bar),
            self._score_direction("SHORT", bar),
        )
        qualified = [
            score
            for score in candidates
            if score.l1 >= self._config.l1_min
            and score.l2 >= self._config.l2_min
            and score.l3 >= self._config.l3_min
            and score.total >= self._config.entry_threshold
        ]
        if not qualified:
            return None
        return max(qualified, key=lambda item: item.total)

    def _score_direction(self, direction: Direction, bar: Bar) -> VwapPullbackScore:
        return VwapPullbackScore(
            direction=direction,
            l1=self._score_trend(direction, bar),
            l2=self._score_position(direction, bar),
            l3=self._score_confirmation(direction, bar),
        )

    def _score_trend(self, direction: Direction, bar: Bar) -> int:
        indicators = self._require_indicators()
        MA_20 = self._required_indicator_value(indicators.MA_20, "MA_20")
        MA_26 = self._required_indicator_value(indicators.MA_26, "MA_26")
        MA_32 = self._required_indicator_value(indicators.MA_32, "MA_32")
        session_vwap = self._required_indicator_value(indicators.VWAP, "VWAP")
        score = 0
        if direction == "LONG":
            if MA_20 > MA_26 > MA_32:
                score += 20
            if bar.close > session_vwap:
                score += 5
            if self._opening_range_high is not None and bar.close >= self._opening_range_high:
                score += 5
        else:
            if MA_20 < MA_26 < MA_32:
                score += 20
            if bar.close < session_vwap:
                score += 5
            if self._opening_range_low is not None and bar.close <= self._opening_range_low:
                score += 5
        return min(score, 30)

    def _score_position(self, direction: Direction, bar: Bar) -> int:
        indicators = self._require_indicators()
        ATR_7 = self._required_indicator_value(indicators.ATR_7, "ATR_7")
        session_vwap = self._required_indicator_value(indicators.VWAP, "VWAP")
        score = 0
        if direction == "LONG":
            pullback_distance = abs(bar.low - session_vwap)
            if (
                bar.low <= session_vwap
                and bar.close > session_vwap
                and pullback_distance <= ATR_7 * self._config.max_pullback_atr
            ):
                score += 20
            if self._near_level(bar.low, self._opening_range_low, ATR_7) or self._near_level(
                bar.low, self._prior_session_low, ATR_7
            ):
                score += 10
        else:
            pullback_distance = abs(bar.high - session_vwap)
            if (
                bar.high >= session_vwap
                and bar.close < session_vwap
                and pullback_distance <= ATR_7 * self._config.max_pullback_atr
            ):
                score += 20
            if self._near_level(bar.high, self._opening_range_high, ATR_7) or self._near_level(
                bar.high, self._prior_session_high, ATR_7
            ):
                score += 10
        return min(score, 30)

    def _score_confirmation(self, direction: Direction, bar: Bar) -> int:
        indicators = self._require_indicators()
        RSI_14 = self._required_indicator_value(indicators.RSI_14, "RSI_14")
        volume_ratio = self._required_indicator_value(indicators.volume_ratio, "volume_ratio")
        body = bar.close - bar.open
        score = 0
        if direction == "LONG" and body > Decimal("0"):
            score += 10
        elif direction == "SHORT" and body < Decimal("0"):
            score += 10
        if volume_ratio >= self._config.min_volume_ratio:
            score += 10
        if direction == "LONG" and self._config.min_rsi <= RSI_14 <= self._config.max_rsi:
            score += 10
        elif direction == "SHORT" and self._config.short_min_rsi <= RSI_14 <= (
            self._config.short_max_rsi
        ):
            score += 10
        return min(score, 40)

    def _enter(self, ctx: StrategyContext, bar: Bar, score: VwapPullbackScore) -> None:
        asset = self._require_asset()
        ATR_7 = self._required_indicator_value(self._require_indicators().ATR_7, "ATR_7")
        self._position_direction = score.direction
        self._entry_price = bar.close
        self._last_score = score
        if score.direction == "LONG":
            self._stop = bar.close - (ATR_7 * self._config.stop_atr_multiple)
            self._take_profit = bar.close + (ATR_7 * self._config.take_profit_atr_multiple)
            self._trailing_stop = self._stop
            ctx.target_quantity(asset, self._config.target_quantity)
        else:
            self._stop = bar.close + (ATR_7 * self._config.stop_atr_multiple)
            self._take_profit = bar.close - (ATR_7 * self._config.take_profit_atr_multiple)
            self._trailing_stop = self._stop
            ctx.target_quantity(asset, -self._config.target_quantity)

    def _clear_position(self) -> None:
        self._position_direction = None
        self._entry_price = None
        self._stop = None
        self._take_profit = None
        self._trailing_stop = None

    def _near_level(
        self,
        price: Decimal,
        level: Decimal | None,
        ATR_7: Decimal,
    ) -> bool:
        if level is None:
            return False
        return abs(price - level) <= ATR_7 * self._config.key_level_atr

    def _require_asset(self) -> AssetRef:
        if self._asset is None:
            raise RuntimeError("strategy must be initialized before using the asset")
        return self._asset

    def _require_indicators(self) -> VwapPullbackIndicators:
        if self._indicators is None:
            raise RuntimeError("strategy must be initialized before reading indicators")
        return self._indicators

    @staticmethod
    def _required_indicator_value(indicator: AssetIndicator, name: str) -> Decimal:
        value = indicator.value
        if value is None:
            raise RuntimeError(f"{name} indicator is not ready")
        if not isinstance(value, Decimal):
            raise TypeError(f"{name} indicator must produce a Decimal value")
        return value

    @staticmethod
    def _max_decimal(current: Decimal | None, candidate: Decimal) -> Decimal:
        if current is None:
            return candidate
        return max(current, candidate)

    @staticmethod
    def _min_decimal(current: Decimal | None, candidate: Decimal) -> Decimal:
        if current is None:
            return candidate
        return min(current, candidate)


__all__ = [
    "VwapPullbackConfig",
    "VwapPullbackIndicators",
    "VwapPullbackScore",
    "VwapPullbackStrategy",
]
