"""Read-only strategy data view."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk.asset_ref import AssetRef


@dataclass(frozen=True, slots=True, init=False)
class DataView:
    """Time-sliced market data exposed to strategies."""

    _bars: Mapping[InstrumentId, tuple[Bar, ...]]
    as_of: datetime

    def __init__(self, bars: Mapping[InstrumentId, Sequence[Bar]], as_of: datetime) -> None:
        """Create a time-sliced strategy data view from platform-owned bars."""
        object.__setattr__(
            self, "_bars", {instrument_id: tuple(values) for instrument_id, values in bars.items()}
        )
        object.__setattr__(self, "as_of", as_of)

    def close(self, asset: AssetRef) -> Decimal:
        """Return the close price of the asset's latest visible bar."""
        return self.bar(asset).close

    def bar(self, asset: AssetRef) -> Bar:
        """Return the asset's most recent visible bar, raising if none exists."""
        history = self.history(asset, bars=1)
        if not history:
            raise KeyError(f"no bar available for asset: {asset.symbol}")
        return history[-1]

    def history(self, asset: AssetRef, bars: int, timeframe: str | None = None) -> tuple[Bar, ...]:
        """Return up to N complete bars at or before as_of for the asset and timeframe."""
        if bars <= 0:
            raise ValueError("bars must be positive")
        values = self._bars.get(asset.instrument_id, ())
        visible = [
            bar
            for bar in values
            if bar.end_time <= self.as_of
            and bar.is_complete
            and not bar.is_partial
            and (timeframe is None or bar.timeframe == timeframe)
        ]
        return tuple(visible[-bars:])


__all__ = ["DataView"]
