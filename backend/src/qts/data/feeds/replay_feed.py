"""Replay market data from a store."""

from __future__ import annotations

from datetime import datetime

from qts.core.ids import InstrumentId
from qts.data.stores.base import MarketDataStore
from qts.runtime.actors.market_data_actor import MarketDataEvent


class ReplayFeed:
    """Deterministic replay feed over stored bars."""

    def __init__(self, store: MarketDataStore) -> None:
        self._store = store

    def events(
        self,
        *,
        instrument_id: InstrumentId,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> tuple[MarketDataEvent, ...]:
        bars = self._store.read_bars(
            instrument_id=instrument_id,
            timeframe=timeframe,
            start=start,
            end=end,
        )
        return tuple(MarketDataEvent(payload=bar) for bar in bars)


__all__ = ["ReplayFeed"]
