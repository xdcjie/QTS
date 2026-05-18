"""Market data value objects with explicit `[start, end)` bar semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.core.time import TimeInterval, require_aware_datetime


@dataclass(frozen=True, slots=True)
class Bar:
    """OHLCV bar over a half-open interval."""

    instrument_id: InstrumentId
    start_time: datetime
    end_time: datetime
    timeframe: str
    session_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")
    vwap: Decimal | None = None
    open_interest: Decimal | None = None
    trade_count: int | None = None
    is_complete: bool = False
    is_partial: bool = False
    is_synthetic: bool = False

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        TimeInterval(start=self.start_time, end=self.end_time)
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")
        if self.high < max(self.open, self.close):
            raise ValueError("high must be greater than or equal to open and close")
        if self.low > min(self.open, self.close):
            raise ValueError("low must be less than or equal to open and close")
        if self.low > self.high:
            raise ValueError("low must be less than or equal to high")
        self._require_non_negative(self.volume, "volume")
        if self.vwap is not None:
            self._require_non_negative(self.vwap, "vwap")
        if self.open_interest is not None:
            self._require_non_negative(self.open_interest, "open_interest")
        if self.trade_count is not None and self.trade_count < 0:
            raise ValueError("trade_count must be non-negative")

    @property
    def interval(self) -> TimeInterval:
        """Perform interval."""
        return TimeInterval(start=self.start_time, end=self.end_time)

    @staticmethod
    def _require_non_negative(value: Decimal, name: str) -> None:
        """Perform _require_non_negative."""
        if value < Decimal("0"):
            raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class Quote:
    """Top-of-book quote."""

    instrument_id: InstrumentId
    time: datetime
    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal = Decimal("0")
    ask_size: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        require_aware_datetime(self.time, name="time")
        if self.bid_price > self.ask_price:
            raise ValueError("bid_price must be less than or equal to ask_price")
        Bar._require_non_negative(self.bid_size, "bid_size")
        Bar._require_non_negative(self.ask_size, "ask_size")

    @property
    def spread(self) -> Decimal:
        """Perform spread."""
        return self.ask_price - self.bid_price


@dataclass(frozen=True, slots=True)
class Tick:
    """Trade tick."""

    instrument_id: InstrumentId
    time: datetime
    price: Decimal
    size: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        require_aware_datetime(self.time, name="time")
        Bar._require_non_negative(self.size, "size")


__all__ = ["Bar", "Quote", "Tick"]
