"""Incremental technical indicators derived from completed bars."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.indicators.rolling import RollingWindow


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


__all__ = ["AverageTrueRange", "RSI", "SessionVWAP", "VolumeRatio"]
