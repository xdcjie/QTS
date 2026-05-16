"""VWAP pullback strategy example using only the public Strategy SDK."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

from qts.strategy_sdk import AssetRef, Strategy

Direction = Literal["LONG", "SHORT"]


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


class VwapPullbackStrategy(Strategy):
    """Bar-level VWAP pullback strategy with SDK-managed indicators."""

    def __init__(self, config: VwapPullbackConfig | None = None, **overrides: Any) -> None:
        if config is not None and overrides:
            raise ValueError("pass either config or constructor overrides, not both")
        if config is None:
            config = VwapPullbackConfig(**overrides)
        self._config = config
        self._asset: AssetRef | None = None
        self._MA_20: Any = None
        self._MA_26: Any = None
        self._MA_32: Any = None
        self._ATR_7: Any = None
        self._RSI_14: Any = None
        self._VWAP: Any = None
        self._volume_ratio: Any = None
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

    def initialize(self, ctx: Any) -> None:
        self._asset = ctx.symbol(self._config.symbol)
        self._MA_20 = ctx.indicator.ema(self._asset, self._config.ma_20_window)
        self._MA_26 = ctx.indicator.ema(self._asset, self._config.ma_26_window)
        self._MA_32 = ctx.indicator.ema(self._asset, self._config.ma_32_window)
        self._ATR_7 = ctx.indicator.atr(self._asset, self._config.atr_window)
        self._RSI_14 = ctx.indicator.rsi(self._asset, self._config.rsi_window)
        self._VWAP = ctx.indicator.session_vwap(self._asset)
        self._volume_ratio = ctx.indicator.volume_ratio(
            self._asset, self._config.volume_ratio_window
        )
        ctx.subscribe(
            self._asset,
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

    def on_bar(self, ctx: Any, bar: Any) -> None:
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

    def _record_session_bar(self, bar: Any) -> None:
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

    def _manage_exit(self, ctx: Any, bar: Any) -> None:
        if self._position_direction is None or self._entry_price is None:
            return
        ATR_7 = self._ATR_7.value
        if ATR_7 is None:
            return

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
            ctx.close(self._asset)
            self._clear_position()

    def _indicators_ready(self) -> bool:
        indicators = (
            self._MA_20,
            self._MA_26,
            self._MA_32,
            self._ATR_7,
            self._RSI_14,
            self._VWAP,
            self._volume_ratio,
        )
        return all(indicator.ready and indicator.value is not None for indicator in indicators)

    def _best_entry_score(self, bar: Any) -> VwapPullbackScore | None:
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

    def _score_direction(self, direction: Direction, bar: Any) -> VwapPullbackScore:
        return VwapPullbackScore(
            direction=direction,
            l1=self._score_trend(direction, bar),
            l2=self._score_position(direction, bar),
            l3=self._score_confirmation(direction, bar),
        )

    def _score_trend(self, direction: Direction, bar: Any) -> int:
        MA_20 = self._MA_20.value
        MA_26 = self._MA_26.value
        MA_32 = self._MA_32.value
        session_vwap = self._VWAP.value
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

    def _score_position(self, direction: Direction, bar: Any) -> int:
        ATR_7 = self._ATR_7.value
        session_vwap = self._VWAP.value
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

    def _score_confirmation(self, direction: Direction, bar: Any) -> int:
        RSI_14 = self._RSI_14.value
        volume_ratio = self._volume_ratio.value
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

    def _enter(self, ctx: Any, bar: Any, score: VwapPullbackScore) -> None:
        ATR_7 = self._ATR_7.value
        self._position_direction = score.direction
        self._entry_price = bar.close
        self._last_score = score
        if score.direction == "LONG":
            self._stop = bar.close - (ATR_7 * self._config.stop_atr_multiple)
            self._take_profit = bar.close + (ATR_7 * self._config.take_profit_atr_multiple)
            self._trailing_stop = self._stop
            ctx.target_quantity(self._asset, self._config.target_quantity)
        else:
            self._stop = bar.close + (ATR_7 * self._config.stop_atr_multiple)
            self._take_profit = bar.close - (ATR_7 * self._config.take_profit_atr_multiple)
            self._trailing_stop = self._stop
            ctx.target_quantity(self._asset, -self._config.target_quantity)

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


__all__ = ["VwapPullbackConfig", "VwapPullbackScore", "VwapPullbackStrategy"]
