"""Historical data portal for backtests."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, DataView


class HistoricalDataPortal:
    """Returns finalized bars visible as of a replay timestamp."""

    def __init__(self, bars: Mapping[InstrumentId, Iterable[Bar]]) -> None:
        self._bars = {
            instrument_id: tuple(sorted(values, key=lambda bar: bar.end_time))
            for instrument_id, values in bars.items()
        }

    def data_view(self, *, as_of: datetime) -> DataView:
        return DataView(bars=self._bars, as_of=as_of)

    def history(
        self,
        asset: AssetRef,
        *,
        as_of: datetime,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[Bar, ...]:
        return self.data_view(as_of=as_of).history(asset, bars=bars, timeframe=timeframe)


__all__ = ["HistoricalDataPortal"]
