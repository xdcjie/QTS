"""Replay market data from a store."""

from __future__ import annotations

from datetime import datetime

from qts.core.ids import InstrumentId
from qts.data.stores.base import MarketDataStore
from qts.domain.market_data import Bar


class ReplayFeed:
    """Deterministic replay feed over stored bars."""

    def __init__(self, store: MarketDataStore) -> None:
        """Bind the feed to the market data store it replays bars from."""
        self._store = store

    def events(
        self,
        *,
        instrument_id: InstrumentId,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> tuple[Bar, ...]:
        """Return stored bars for an instrument and timeframe within [start, end)."""
        return self._store.read_bars(
            instrument_id=instrument_id,
            timeframe=timeframe,
            start=start,
            end=end,
        )


__all__ = ["ReplayFeed"]
