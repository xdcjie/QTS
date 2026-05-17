"""Read-only strategy portfolio view."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding
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
    holdings: Mapping[InstrumentId, Holding] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        object.__setattr__(self, "positions", MappingProxyType(dict(self.positions)))
        object.__setattr__(self, "holdings", MappingProxyType(dict(self.holdings)))

    def position(self, asset: AssetRef) -> PortfolioPosition:
        """Perform position."""
        return self.positions.get(asset.instrument_id, PortfolioPosition())

    def exposure(self, asset: AssetRef) -> Decimal:
        """Perform exposure."""
        return self.position(asset).market_value

    def holding(self, asset: AssetRef) -> Holding | None:
        """Return the holding snapshot for an asset."""
        return self.holdings.get(asset.instrument_id)

    def unrealized_pnl(
        self,
        asset: AssetRef,
        *,
        mark_price: Decimal | None = None,
        multiplier: Decimal = Decimal("1"),
    ) -> Decimal:
        """Return unrealized PnL for an asset when a mark is supplied."""
        holding = self.holding(asset)
        if holding is None:
            return Decimal("0")
        if mark_price is None:
            return Decimal("0")
        return holding.unrealized_pnl(mark_price, multiplier)

    def realized_pnl(self, asset: AssetRef) -> Decimal:
        """Return cumulative realized PnL for an asset."""
        holding = self.holding(asset)
        return Decimal("0") if holding is None else holding.realized_pnl

    def avg_cost(self, asset: AssetRef) -> Decimal | None:
        """Return average cost for an asset holding."""
        holding = self.holding(asset)
        return None if holding is None else holding.average_cost

    def weight(self, asset: AssetRef) -> Decimal:
        """Perform weight."""
        if self.equity == Decimal("0"):
            return Decimal("0")
        return self.exposure(asset) / self.equity


__all__ = ["PortfolioPosition", "PortfolioView"]
