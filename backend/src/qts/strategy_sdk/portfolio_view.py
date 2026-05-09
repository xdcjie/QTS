"""Read-only strategy portfolio view."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType

from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    """Read-only position snapshot."""

    quantity: Decimal = Decimal("0")
    market_value: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class PortfolioView:
    """Immutable user-facing portfolio snapshot."""

    cash: Decimal
    equity: Decimal
    positions: Mapping[InstrumentId, PortfolioPosition] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "positions", MappingProxyType(dict(self.positions)))

    def position(self, asset: AssetRef) -> PortfolioPosition:
        return self.positions.get(asset.instrument_id, PortfolioPosition())

    def exposure(self, asset: AssetRef) -> Decimal:
        return self.position(asset).market_value

    def weight(self, asset: AssetRef) -> Decimal:
        if self.equity == Decimal("0"):
            return Decimal("0")
        return self.exposure(asset) / self.equity


__all__ = ["PortfolioPosition", "PortfolioView"]
