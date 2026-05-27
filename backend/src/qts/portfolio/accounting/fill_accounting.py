"""Apply fills to cash and positions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import OrderSide
from qts.portfolio.cash_book import CashBook
from qts.portfolio.holdings import HoldingBook


@dataclass(frozen=True, slots=True)
class AccountingFill:
    """Executed fill used by accounting."""

    fill_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
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
    def apply(
        fill: AccountingFill,
        *,
        cash_book: CashBook,
        holding_book: HoldingBook,
    ) -> None:
        """Perform apply."""
        signed_quantity = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity
        cash_delta = -signed_quantity * fill.price * fill.multiplier
        holding_book.apply_fill(
            instrument_id=fill.instrument_id,
            signed_quantity=signed_quantity,
            price=fill.price,
            multiplier=fill.multiplier,
            fill_time=None,
        )
        cash_book.apply_delta(fill.currency, cash_delta)


__all__ = ["AccountingFill", "FillAccounting"]
