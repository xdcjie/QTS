"""Apply fills to cash and positions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from qts.core.ids import InstrumentId, OrderId
from qts.portfolio.cash_book import CashBook
from qts.portfolio.position_book import PositionBook


class TradeSide(StrEnum):
    """Fill side."""

    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Fill:
    """Executed fill used by accounting."""

    fill_id: OrderId
    instrument_id: InstrumentId
    side: TradeSide
    quantity: Decimal
    price: Decimal
    currency: str
    multiplier: Decimal

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.price < Decimal("0"):
            raise ValueError("price must be non-negative")
        if self.multiplier <= Decimal("0"):
            raise ValueError("multiplier must be positive")
        if not self.currency.strip():
            raise ValueError("currency must not be empty")


class FillAccounting:
    """Fill accounting operations."""

    @staticmethod
    def apply(fill: Fill, *, cash_book: CashBook, position_book: PositionBook) -> None:
        """Perform apply."""
        signed_quantity = fill.quantity if fill.side is TradeSide.BUY else -fill.quantity
        cash_delta = -signed_quantity * fill.price * fill.multiplier
        position_book.apply_delta(fill.instrument_id, signed_quantity)
        cash_book.apply_delta(fill.currency, cash_delta)


__all__ = ["Fill", "FillAccounting", "TradeSide"]
