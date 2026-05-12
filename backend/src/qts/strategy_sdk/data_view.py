"""Read-only strategy data view."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk.asset_ref import AssetRef


@dataclass(frozen=True, slots=True)
class DataView:
    """Time-sliced market data exposed to strategies."""

    bars: Mapping[InstrumentId, Sequence[Bar]]
    as_of: datetime

    def close(self, asset: AssetRef) -> Decimal:
        """Perform close."""
        return self.bar(asset).close

    def bar(self, asset: AssetRef) -> Bar:
        """Perform bar."""
        history = self.history(asset, bars=1)
        if not history:
            raise KeyError(f"no bar available for asset: {asset.symbol}")
        return history[-1]

    def history(self, asset: AssetRef, bars: int, timeframe: str | None = None) -> tuple[Bar, ...]:
        """Perform history."""
        if bars <= 0:
            raise ValueError("bars must be positive")
        values = self.bars.get(asset.instrument_id, ())
        visible = [
            bar
            for bar in values
            if bar.end_time <= self.as_of
            and bar.is_complete
            and not bar.is_partial
            and (timeframe is None or bar.timeframe == timeframe)
        ]
        return tuple(visible[-bars:])


class MarketDataPortal:
    """Build source- and mode-agnostic strategy data views from finalized bars."""

    def __init__(self, bars: Mapping[InstrumentId, Iterable[Bar]]) -> None:
        """Normalize finalized bar history by instrument."""
        self._bars = {
            instrument_id: tuple(sorted(values, key=lambda bar: bar.end_time))
            for instrument_id, values in bars.items()
        }

    def data_view(self, *, as_of: datetime) -> DataView:
        """Return the strategy-facing data view for one logical timestamp."""
        return DataView(bars=self._bars, as_of=as_of)

    def history(
        self,
        asset: AssetRef,
        *,
        as_of: datetime,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[Bar, ...]:
        """Return finalized bar history visible to a strategy at as_of."""
        return self.data_view(as_of=as_of).history(asset, bars=bars, timeframe=timeframe)


__all__ = ["DataView", "MarketDataPortal"]
