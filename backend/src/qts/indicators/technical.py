"""Incremental technical indicators derived from completed bars."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.indicators.price.ema import EMA
from qts.indicators.rolling import RollingWindow


def _typical_price(bar: Bar) -> Decimal:
    return (bar.high + bar.low + bar.close) / Decimal("3")


def _population_standard_deviation(values: tuple[Decimal, ...]) -> Decimal:
    mean = sum(values, Decimal("0")) / Decimal(len(values))
    variance = sum((item - mean) * (item - mean) for item in values) / Decimal(len(values))
    return variance.sqrt()


def _money_flow_volume(bar: Bar) -> Decimal:
    price_range = bar.high - bar.low
    if price_range == Decimal("0"):
        return Decimal("0")
    multiplier = ((bar.close - bar.low) - (bar.high - bar.close)) / price_range
    return multiplier * bar.volume


@dataclass(slots=True)
class AverageTrueRange:
    """Wilder average true range over completed bars."""

    window: int
    _true_ranges: RollingWindow[Decimal] = field(init=False, repr=False)
    _previous_close: Decimal | None = field(default=None, init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize ATR state."""
        self._true_ranges = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether ATR has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal | None:
        """Update ATR from a completed OHLC bar."""
        return self.update(high=bar.high, low=bar.low, close=bar.close)

    def update(self, *, high: Decimal, low: Decimal, close: Decimal) -> Decimal | None:
        """Update ATR from OHLC values."""
        true_range = self._true_range(high=high, low=low)
        self._previous_close = close
        if self.value is None:
            self._true_ranges.append(true_range)
            if not self._true_ranges.ready:
                return None
            self.value = sum(self._true_ranges, Decimal("0")) / Decimal(self.window)
            return self.value
        self.value = (self.value * Decimal(self.window - 1) + true_range) / Decimal(self.window)
        return self.value

    def _true_range(self, *, high: Decimal, low: Decimal) -> Decimal:
        """Return true range using the previous close when available."""
        if self._previous_close is None:
            return high - low
        return max(high - low, abs(high - self._previous_close), abs(low - self._previous_close))


@dataclass(slots=True)
class RSI:
    """Relative strength index using Wilder smoothing."""

    window: int
    _gains: RollingWindow[Decimal] = field(init=False, repr=False)
    _losses: RollingWindow[Decimal] = field(init=False, repr=False)
    _previous_price: Decimal | None = field(default=None, init=False, repr=False)
    _average_gain: Decimal | None = field(default=None, init=False, repr=False)
    _average_loss: Decimal | None = field(default=None, init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize RSI state."""
        self._gains = RollingWindow[Decimal](self.window)
        self._losses = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether RSI has warmed up."""
        return self.value is not None

    def update(self, price: Decimal) -> Decimal | None:
        """Update RSI from a close price."""
        if self._previous_price is None:
            self._previous_price = price
            return None
        change = price - self._previous_price
        self._previous_price = price
        gain = max(change, Decimal("0"))
        loss = abs(min(change, Decimal("0")))
        if self.value is None:
            self._gains.append(gain)
            self._losses.append(loss)
            if not self._gains.ready:
                return None
            self._average_gain = sum(self._gains, Decimal("0")) / Decimal(self.window)
            self._average_loss = sum(self._losses, Decimal("0")) / Decimal(self.window)
        else:
            if self._average_gain is None or self._average_loss is None:
                raise RuntimeError("RSI smoothing state is not initialized")
            self._average_gain = (self._average_gain * Decimal(self.window - 1) + gain) / Decimal(
                self.window
            )
            self._average_loss = (self._average_loss * Decimal(self.window - 1) + loss) / Decimal(
                self.window
            )
        self.value = self._rsi_from_averages()
        return self.value

    def _rsi_from_averages(self) -> Decimal:
        """Compute RSI from initialized average gain/loss values."""
        if self._average_gain is None or self._average_loss is None:
            raise RuntimeError("RSI smoothing state is not initialized")
        if self._average_loss == Decimal("0"):
            return Decimal("100")
        relative_strength = self._average_gain / self._average_loss
        return Decimal("100") - (Decimal("100") / (Decimal("1") + relative_strength))


@dataclass(slots=True)
class SessionVWAP:
    """Session VWAP that resets on `Bar.session_id` changes."""

    _session_id: str | None = field(default=None, init=False, repr=False)
    _cumulative_price_volume: Decimal = field(default=Decimal("0"), init=False, repr=False)
    _cumulative_volume: Decimal = field(default=Decimal("0"), init=False, repr=False)
    value: Decimal | None = None

    @property
    def ready(self) -> bool:
        """Return whether the current session has a VWAP value."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal | None:
        """Update VWAP from a completed OHLCV bar."""
        if bar.session_id != self._session_id:
            self._session_id = bar.session_id
            self._cumulative_price_volume = Decimal("0")
            self._cumulative_volume = Decimal("0")
            self.value = None

        typical_price = (bar.high + bar.low + bar.close) / Decimal("3")
        self._cumulative_price_volume += typical_price * bar.volume
        self._cumulative_volume += bar.volume
        if self._cumulative_volume == Decimal("0"):
            return None
        self.value = self._cumulative_price_volume / self._cumulative_volume
        return self.value


@dataclass(slots=True)
class VolumeRatio:
    """Current volume divided by the rolling average volume."""

    window: int
    _volumes: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize rolling volume state."""
        self._volumes = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether volume ratio has warmed up."""
        return self.value is not None

    def update(self, volume: Decimal) -> Decimal | None:
        """Update the ratio from a volume observation."""
        self._volumes.append(volume)
        if not self._volumes.ready:
            self.value = None
            return None
        average = sum(self._volumes, Decimal("0")) / Decimal(self.window)
        if average == Decimal("0"):
            self.value = Decimal("1")
        else:
            self.value = volume / average
        return self.value


@dataclass(frozen=True, slots=True)
class BollingerBandsValue:
    """Bollinger Bands output for a completed price update."""

    lower: Decimal
    middle: Decimal
    upper: Decimal
    standard_deviation: Decimal


@dataclass(slots=True)
class BollingerBands:
    """Bollinger Bands using population standard deviation."""

    window: int
    standard_deviations: Decimal = Decimal("2")
    _prices: RollingWindow[Decimal] = field(init=False, repr=False)
    value: BollingerBandsValue | None = None

    def __post_init__(self) -> None:
        """Validate and initialize rolling price state."""
        if self.standard_deviations < Decimal("0"):
            raise ValueError("standard_deviations must be non-negative")
        self._prices = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether the bands have warmed up."""
        return self.value is not None

    def update(self, price: Decimal) -> BollingerBandsValue | None:
        """Update Bollinger Bands from a close price."""
        self._prices.append(price)
        if not self._prices.ready:
            self.value = None
            return None
        prices = self._prices.snapshot()
        middle = sum(prices, Decimal("0")) / Decimal(self.window)
        variance = sum((item - middle) * (item - middle) for item in prices) / Decimal(self.window)
        standard_deviation = variance.sqrt()
        offset = self.standard_deviations * standard_deviation
        self.value = BollingerBandsValue(
            lower=middle - offset,
            middle=middle,
            upper=middle + offset,
            standard_deviation=standard_deviation,
        )
        return self.value


@dataclass(frozen=True, slots=True)
class MACDValue:
    """MACD output for a completed price update."""

    macd: Decimal
    signal: Decimal
    histogram: Decimal


@dataclass(slots=True)
class MACD:
    """Moving Average Convergence Divergence with SMA-seeded EMAs."""

    fast_window: int
    slow_window: int
    signal_window: int
    _fast: EMA = field(init=False, repr=False)
    _slow: EMA = field(init=False, repr=False)
    _signal: EMA = field(init=False, repr=False)
    value: MACDValue | None = None

    def __post_init__(self) -> None:
        """Validate and initialize MACD EMA state."""
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window must be less than slow_window")
        self._fast = EMA(window=self.fast_window)
        self._slow = EMA(window=self.slow_window)
        self._signal = EMA(window=self.signal_window)

    @property
    def ready(self) -> bool:
        """Return whether MACD and signal have warmed up."""
        return self.value is not None

    def update(self, price: Decimal) -> MACDValue | None:
        """Update MACD from a close price."""
        fast = self._fast.update(price)
        slow = self._slow.update(price)
        if fast is None or slow is None:
            self.value = None
            return None

        macd = fast - slow
        signal = self._signal.update(macd)
        if signal is None:
            self.value = None
            return None

        self.value = MACDValue(macd=macd, signal=signal, histogram=macd - signal)
        return self.value


@dataclass(slots=True)
class RateOfChange:
    """Rate of change percentage versus the price `window` periods ago."""

    window: int
    _prices: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize rolling price state."""
        self._prices = RollingWindow[Decimal](self.window + 1)

    @property
    def ready(self) -> bool:
        """Return whether rate of change has warmed up."""
        return self.value is not None

    def update(self, price: Decimal) -> Decimal | None:
        """Update rate of change from a close price."""
        self._prices.append(price)
        if not self._prices.ready:
            self.value = None
            return None
        previous = self._prices.snapshot()[0]
        if previous == Decimal("0"):
            self.value = None
            return None
        self.value = ((price - previous) / previous) * Decimal("100")
        return self.value


@dataclass(frozen=True, slots=True)
class DirectionalMovementValue:
    """ADX output for a completed bar update."""

    plus_di: Decimal
    minus_di: Decimal
    dx: Decimal
    adx: Decimal


@dataclass(slots=True)
class ADX:
    """Average Directional Index using Wilder smoothing."""

    window: int
    _true_ranges: RollingWindow[Decimal] = field(init=False, repr=False)
    _plus_dm_values: RollingWindow[Decimal] = field(init=False, repr=False)
    _minus_dm_values: RollingWindow[Decimal] = field(init=False, repr=False)
    _previous_high: Decimal | None = field(default=None, init=False, repr=False)
    _previous_low: Decimal | None = field(default=None, init=False, repr=False)
    _previous_close: Decimal | None = field(default=None, init=False, repr=False)
    _average_true_range: Decimal | None = field(default=None, init=False, repr=False)
    _average_plus_dm: Decimal | None = field(default=None, init=False, repr=False)
    _average_minus_dm: Decimal | None = field(default=None, init=False, repr=False)
    value: DirectionalMovementValue | None = None

    def __post_init__(self) -> None:
        """Validate and initialize directional movement state."""
        self._true_ranges = RollingWindow[Decimal](self.window)
        self._plus_dm_values = RollingWindow[Decimal](self.window)
        self._minus_dm_values = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether ADX has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> DirectionalMovementValue | None:
        """Update ADX from a completed OHLC bar."""
        true_range, plus_dm, minus_dm = self._directional_inputs(bar)
        self._previous_high = bar.high
        self._previous_low = bar.low
        self._previous_close = bar.close
        if self._average_true_range is None:
            self._true_ranges.append(true_range)
            self._plus_dm_values.append(plus_dm)
            self._minus_dm_values.append(minus_dm)
            if not self._true_ranges.ready:
                self.value = None
                return None
            self._average_true_range = sum(self._true_ranges, Decimal("0")) / Decimal(self.window)
            self._average_plus_dm = sum(self._plus_dm_values, Decimal("0")) / Decimal(self.window)
            self._average_minus_dm = sum(self._minus_dm_values, Decimal("0")) / Decimal(self.window)
            dx = self._dx()
            self.value = DirectionalMovementValue(
                plus_di=self._plus_di(),
                minus_di=self._minus_di(),
                dx=dx,
                adx=dx,
            )
            return self.value

        self._average_true_range = (
            self._average_true_range * Decimal(self.window - 1) + true_range
        ) / Decimal(self.window)
        if self._average_plus_dm is None or self._average_minus_dm is None:
            raise RuntimeError("ADX smoothing state is not initialized")
        self._average_plus_dm = (
            self._average_plus_dm * Decimal(self.window - 1) + plus_dm
        ) / Decimal(self.window)
        self._average_minus_dm = (
            self._average_minus_dm * Decimal(self.window - 1) + minus_dm
        ) / Decimal(self.window)
        dx = self._dx()
        previous_adx = self.value.adx if self.value is not None else dx
        adx = (previous_adx * Decimal(self.window - 1) + dx) / Decimal(self.window)
        self.value = DirectionalMovementValue(
            plus_di=self._plus_di(),
            minus_di=self._minus_di(),
            dx=dx,
            adx=adx,
        )
        return self.value

    def _directional_inputs(self, bar: Bar) -> tuple[Decimal, Decimal, Decimal]:
        if self._previous_close is None:
            return bar.high - bar.low, Decimal("0"), Decimal("0")
        true_range = max(
            bar.high - bar.low,
            abs(bar.high - self._previous_close),
            abs(bar.low - self._previous_close),
        )
        up_move = (
            bar.high - self._previous_high if self._previous_high is not None else Decimal("0")
        )
        down_move = self._previous_low - bar.low if self._previous_low is not None else Decimal("0")
        plus_dm = up_move if up_move > down_move and up_move > Decimal("0") else Decimal("0")
        minus_dm = down_move if down_move > up_move and down_move > Decimal("0") else Decimal("0")
        return true_range, plus_dm, minus_dm

    def _plus_di(self) -> Decimal:
        average_true_range = self._average_true_range
        if (
            average_true_range is None
            or average_true_range == Decimal("0")
            or self._average_plus_dm is None
        ):
            return Decimal("0")
        return (self._average_plus_dm / average_true_range) * Decimal("100")

    def _minus_di(self) -> Decimal:
        average_true_range = self._average_true_range
        if (
            average_true_range is None
            or average_true_range == Decimal("0")
            or self._average_minus_dm is None
        ):
            return Decimal("0")
        return (self._average_minus_dm / average_true_range) * Decimal("100")

    def _dx(self) -> Decimal:
        plus_di = self._plus_di()
        minus_di = self._minus_di()
        total = plus_di + minus_di
        if total == Decimal("0"):
            return Decimal("0")
        return (abs(plus_di - minus_di) / total) * Decimal("100")


@dataclass(frozen=True, slots=True)
class KeltnerChannelValue:
    """Keltner Channel output for a completed bar update."""

    lower: Decimal
    middle: Decimal
    upper: Decimal
    atr: Decimal


@dataclass(slots=True)
class KeltnerChannel:
    """Keltner Channel using EMA middle and ATR width."""

    window: int
    multiplier: Decimal = Decimal("2")
    _middle: EMA = field(init=False, repr=False)
    _atr: AverageTrueRange = field(init=False, repr=False)
    value: KeltnerChannelValue | None = None

    def __post_init__(self) -> None:
        """Validate and initialize Keltner Channel state."""
        if self.multiplier < Decimal("0"):
            raise ValueError("multiplier must be non-negative")
        self._middle = EMA(window=self.window)
        self._atr = AverageTrueRange(window=self.window)

    @property
    def ready(self) -> bool:
        """Return whether the channel has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> KeltnerChannelValue | None:
        """Update Keltner Channel from a completed OHLC bar."""
        middle = self._middle.update(bar.close)
        atr = self._atr.update_bar(bar)
        if middle is None or atr is None:
            self.value = None
            return None
        width = atr * self.multiplier
        self.value = KeltnerChannelValue(
            lower=middle - width,
            middle=middle,
            upper=middle + width,
            atr=atr,
        )
        return self.value


@dataclass(frozen=True, slots=True)
class DonchianChannelValue:
    """Donchian Channel output for a completed bar update."""

    lower: Decimal
    middle: Decimal
    upper: Decimal


@dataclass(slots=True)
class DonchianChannel:
    """Donchian Channel over rolling high and low values."""

    window: int
    _highs: RollingWindow[Decimal] = field(init=False, repr=False)
    _lows: RollingWindow[Decimal] = field(init=False, repr=False)
    value: DonchianChannelValue | None = None

    def __post_init__(self) -> None:
        """Validate and initialize Donchian Channel state."""
        self._highs = RollingWindow[Decimal](self.window)
        self._lows = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether the channel has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> DonchianChannelValue | None:
        """Update Donchian Channel from a completed OHLC bar."""
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        if not self._highs.ready:
            self.value = None
            return None
        upper = max(self._highs)
        lower = min(self._lows)
        self.value = DonchianChannelValue(
            lower=lower,
            middle=(upper + lower) / Decimal("2"),
            upper=upper,
        )
        return self.value


@dataclass(frozen=True, slots=True)
class StochasticOscillatorValue:
    """Stochastic oscillator output for a completed bar update."""

    percent_k: Decimal
    percent_d: Decimal


@dataclass(slots=True)
class StochasticOscillator:
    """Stochastic oscillator with rolling %K and SMA %D."""

    window: int
    signal_window: int = 3
    _highs: RollingWindow[Decimal] = field(init=False, repr=False)
    _lows: RollingWindow[Decimal] = field(init=False, repr=False)
    _percent_k: RollingWindow[Decimal] = field(init=False, repr=False)
    value: StochasticOscillatorValue | None = None

    def __post_init__(self) -> None:
        """Validate and initialize stochastic oscillator state."""
        self._highs = RollingWindow[Decimal](self.window)
        self._lows = RollingWindow[Decimal](self.window)
        self._percent_k = RollingWindow[Decimal](self.signal_window)

    @property
    def ready(self) -> bool:
        """Return whether the oscillator has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> StochasticOscillatorValue | None:
        """Update stochastic oscillator from a completed OHLC bar."""
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        if not self._highs.ready:
            self.value = None
            return None
        highest_high = max(self._highs)
        lowest_low = min(self._lows)
        price_range = highest_high - lowest_low
        percent_k = (
            Decimal("0")
            if price_range == Decimal("0")
            else ((bar.close - lowest_low) / price_range) * Decimal("100")
        )
        self._percent_k.append(percent_k)
        if not self._percent_k.ready:
            self.value = None
            return None
        percent_d = sum(self._percent_k, Decimal("0")) / Decimal(self.signal_window)
        self.value = StochasticOscillatorValue(percent_k=percent_k, percent_d=percent_d)
        return self.value


@dataclass(slots=True)
class CommodityChannelIndex:
    """Commodity Channel Index over rolling typical prices."""

    window: int
    _typical_prices: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize CCI state."""
        self._typical_prices = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether CCI has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal | None:
        """Update CCI from a completed OHLC bar."""
        typical_price = _typical_price(bar)
        self._typical_prices.append(typical_price)
        if not self._typical_prices.ready:
            self.value = None
            return None
        prices = self._typical_prices.snapshot()
        average = sum(prices, Decimal("0")) / Decimal(self.window)
        mean_deviation = sum(abs(item - average) for item in prices) / Decimal(self.window)
        if mean_deviation == Decimal("0"):
            self.value = Decimal("0")
        else:
            self.value = (typical_price - average) / (Decimal("0.015") * mean_deviation)
        return self.value


@dataclass(slots=True)
class WilliamsR:
    """Williams %R over rolling high and low values."""

    window: int
    _highs: RollingWindow[Decimal] = field(init=False, repr=False)
    _lows: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize Williams %R state."""
        self._highs = RollingWindow[Decimal](self.window)
        self._lows = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether Williams %R has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal | None:
        """Update Williams %R from a completed OHLC bar."""
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        if not self._highs.ready:
            self.value = None
            return None
        highest_high = max(self._highs)
        lowest_low = min(self._lows)
        price_range = highest_high - lowest_low
        self.value = (
            Decimal("0")
            if price_range == Decimal("0")
            else ((highest_high - bar.close) / price_range) * Decimal("-100")
        )
        return self.value


@dataclass(slots=True)
class StandardDeviation:
    """Rolling population standard deviation of close prices."""

    window: int
    _prices: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize standard deviation state."""
        self._prices = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether standard deviation has warmed up."""
        return self.value is not None

    def update(self, price: Decimal) -> Decimal | None:
        """Update standard deviation from a close price."""
        self._prices.append(price)
        if not self._prices.ready:
            self.value = None
            return None
        self.value = _population_standard_deviation(self._prices.snapshot())
        return self.value


@dataclass(slots=True)
class HistoricalVolatility:
    """Annualized rolling volatility of simple close-to-close returns."""

    window: int
    periods_per_year: Decimal = Decimal("252")
    _returns: RollingWindow[Decimal] = field(init=False, repr=False)
    _previous_price: Decimal | None = field(default=None, init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize historical volatility state."""
        if self.periods_per_year <= Decimal("0"):
            raise ValueError("periods_per_year must be positive")
        self._returns = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether historical volatility has warmed up."""
        return self.value is not None

    def update(self, price: Decimal) -> Decimal | None:
        """Update historical volatility from a close price."""
        if self._previous_price is None:
            self._previous_price = price
            return None
        previous = self._previous_price
        self._previous_price = price
        if previous == Decimal("0"):
            self.value = None
            return None
        self._returns.append((price - previous) / previous)
        if not self._returns.ready:
            self.value = None
            return None
        self.value = (
            _population_standard_deviation(self._returns.snapshot()) * self.periods_per_year.sqrt()
        )
        return self.value


@dataclass(slots=True)
class OnBalanceVolume:
    """On-Balance Volume cumulative volume indicator."""

    _previous_close: Decimal | None = field(default=None, init=False, repr=False)
    value: Decimal | None = None

    @property
    def ready(self) -> bool:
        """Return whether OBV has processed at least one close."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal | None:
        """Update OBV from a completed OHLCV bar."""
        return self.update(close=bar.close, volume=bar.volume)

    def update(self, *, close: Decimal, volume: Decimal) -> Decimal:
        """Update OBV from close and volume values."""
        if self._previous_close is None:
            self._previous_close = close
            self.value = Decimal("0")
            return self.value
        if self.value is None:
            raise RuntimeError("OBV cumulative state is not initialized")
        if close > self._previous_close:
            self.value += volume
        elif close < self._previous_close:
            self.value -= volume
        self._previous_close = close
        return self.value


@dataclass(slots=True)
class MoneyFlowIndex:
    """Money Flow Index over rolling positive and negative money flow."""

    window: int
    _positive_flows: RollingWindow[Decimal] = field(init=False, repr=False)
    _negative_flows: RollingWindow[Decimal] = field(init=False, repr=False)
    _previous_typical_price: Decimal | None = field(default=None, init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize MFI state."""
        self._positive_flows = RollingWindow[Decimal](self.window)
        self._negative_flows = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether MFI has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal | None:
        """Update MFI from a completed OHLCV bar."""
        typical_price = _typical_price(bar)
        if self._previous_typical_price is None:
            self._previous_typical_price = typical_price
            return None
        raw_money_flow = typical_price * bar.volume
        positive_flow = Decimal("0")
        negative_flow = Decimal("0")
        if typical_price > self._previous_typical_price:
            positive_flow = raw_money_flow
        elif typical_price < self._previous_typical_price:
            negative_flow = raw_money_flow
        self._previous_typical_price = typical_price
        self._positive_flows.append(positive_flow)
        self._negative_flows.append(negative_flow)
        if not self._positive_flows.ready:
            self.value = None
            return None
        positive_total = sum(self._positive_flows, Decimal("0"))
        negative_total = sum(self._negative_flows, Decimal("0"))
        if negative_total == Decimal("0"):
            self.value = Decimal("100")
        else:
            money_ratio = positive_total / negative_total
            self.value = Decimal("100") - (Decimal("100") / (Decimal("1") + money_ratio))
        return self.value


@dataclass(slots=True)
class AccumulationDistribution:
    """Accumulation/Distribution Line cumulative money flow volume."""

    value: Decimal | None = None

    @property
    def ready(self) -> bool:
        """Return whether ADL has processed at least one bar."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal:
        """Update ADL from a completed OHLCV bar."""
        if self.value is None:
            self.value = Decimal("0")
        self.value += _money_flow_volume(bar)
        return self.value


@dataclass(slots=True)
class ChaikinMoneyFlow:
    """Chaikin Money Flow over rolling money flow volume."""

    window: int
    _money_flow_volumes: RollingWindow[Decimal] = field(init=False, repr=False)
    _volumes: RollingWindow[Decimal] = field(init=False, repr=False)
    value: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate and initialize CMF state."""
        self._money_flow_volumes = RollingWindow[Decimal](self.window)
        self._volumes = RollingWindow[Decimal](self.window)

    @property
    def ready(self) -> bool:
        """Return whether CMF has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> Decimal | None:
        """Update CMF from a completed OHLCV bar."""
        self._money_flow_volumes.append(_money_flow_volume(bar))
        self._volumes.append(bar.volume)
        if not self._money_flow_volumes.ready:
            self.value = None
            return None
        volume_total = sum(self._volumes, Decimal("0"))
        if volume_total == Decimal("0"):
            self.value = Decimal("0")
        else:
            self.value = sum(self._money_flow_volumes, Decimal("0")) / volume_total
        return self.value


__all__ = [
    "ADX",
    "AccumulationDistribution",
    "AverageTrueRange",
    "BollingerBands",
    "BollingerBandsValue",
    "ChaikinMoneyFlow",
    "CommodityChannelIndex",
    "DirectionalMovementValue",
    "DonchianChannel",
    "DonchianChannelValue",
    "HistoricalVolatility",
    "KeltnerChannel",
    "KeltnerChannelValue",
    "MACD",
    "MACDValue",
    "MoneyFlowIndex",
    "OnBalanceVolume",
    "RSI",
    "RateOfChange",
    "SessionVWAP",
    "StandardDeviation",
    "StochasticOscillator",
    "StochasticOscillatorValue",
    "VolumeRatio",
    "WilliamsR",
]
