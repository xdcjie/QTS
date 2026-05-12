"""Deterministic in-memory market data store."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


class InMemoryMarketDataStore:
    """In-memory bar store for tests and local runs."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._bars: dict[tuple[InstrumentId, str], list[Bar]] = defaultdict(list)

    def write_bars(self, bars: Iterable[Bar]) -> None:
        """Perform write_bars."""
        for bar in bars:
            key = (bar.instrument_id, bar.timeframe)
            self._bars[key].append(bar)
            self._bars[key].sort(key=lambda item: (item.start_time, item.end_time))

    def read_bars(
        self,
        *,
        instrument_id: InstrumentId,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> tuple[Bar, ...]:
        """Perform read_bars."""
        return tuple(
            bar
            for bar in self._bars.get((instrument_id, timeframe), ())
            if start <= bar.start_time and bar.end_time <= end
        )


__all__ = ["InMemoryMarketDataStore"]
