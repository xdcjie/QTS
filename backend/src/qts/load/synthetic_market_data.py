"""Deterministic synthetic market data generation for load tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


@dataclass(frozen=True, slots=True)
class SyntheticMarketDataConfig:
    """Configuration for deterministic synthetic market data."""

    instrument_id: InstrumentId
    start: datetime
    count: int
    timeframe: str
    start_price: Decimal
    step: Decimal
    session_id: str

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("count must be positive")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if not self.session_id.strip():
            raise ValueError("session_id must not be empty")


def generate_bars(config: SyntheticMarketDataConfig) -> tuple[Bar, ...]:
    """Perform generate_bars."""
    bars: list[Bar] = []
    current = config.start_price
    for index in range(config.count):
        open_price = current
        close_price = open_price + config.step
        start = config.start + timedelta(minutes=index)
        bars.append(
            Bar(
                instrument_id=config.instrument_id,
                start_time=start,
                end_time=start + timedelta(minutes=1),
                timeframe=config.timeframe,
                session_id=config.session_id,
                open=open_price,
                high=max(open_price, close_price),
                low=min(open_price, close_price),
                close=close_price,
                volume=Decimal("1"),
                is_complete=True,
            )
        )
        current = close_price
    return tuple(bars)


__all__ = ["SyntheticMarketDataConfig", "generate_bars"]
