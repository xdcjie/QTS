"""Market data store interface."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


class MarketDataStore(Protocol):
    """Store and read bars by internal instrument identity."""

    def write_bars(self, bars: Iterable[Bar]) -> None: ...

    def read_bars(
        self,
        *,
        instrument_id: InstrumentId,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> tuple[Bar, ...]: ...


__all__ = ["MarketDataStore"]
