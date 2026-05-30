"""Order event DTOs for API and streaming boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OrderFillDTO:
    """Stable fill event shape for public streams."""

    fill_id: str
    order_id: str
    instrument_id: str
    side: str
    quantity: Decimal
    price: Decimal

    def __post_init__(self) -> None:
        """Require non-empty fill, order, instrument, and side identifiers."""
        if not self.fill_id.strip():
            raise ValueError("fill_id must not be empty")
        if not self.order_id.strip():
            raise ValueError("order_id must not be empty")
        if not self.instrument_id.strip():
            raise ValueError("instrument_id must not be empty")
        if not self.side.strip():
            raise ValueError("side must not be empty")


__all__ = ["OrderFillDTO"]
