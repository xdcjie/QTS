"""Account actor MVP."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from qts.core.ids import AccountId, InstrumentId
from qts.execution.idempotency import FillIdempotencyStore
from qts.execution.order_manager import OrderFill, OrderSide
from qts.portfolio.cash_book import CashBook
from qts.portfolio.position_book import Position, PositionBook
from qts.runtime.actor import Actor


@dataclass(frozen=True, slots=True)
class ApplyFill:
    """Message instructing AccountActor to apply a validated fill."""

    fill: OrderFill
    currency: str
    multiplier: Decimal


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """Read-only account snapshot."""

    cash: Mapping[str, Decimal]
    positions: Mapping[InstrumentId, Position]
    account_id: AccountId | None = None


class AccountActor(Actor):
    """Owns account cash and position state."""

    def __init__(
        self,
        initial_cash: Mapping[str, Decimal] | None = None,
        *,
        account_id: AccountId | None = None,
    ) -> None:
        """Perform __init__."""
        self._account_id = account_id
        self._cash = CashBook(initial_cash)
        self._positions = PositionBook()
        self._fill_ids = FillIdempotencyStore()

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, ApplyFill):
            self._apply_fill(message)
            return
        raise TypeError(f"unsupported account message: {type(message).__name__}")

    def snapshot(self) -> AccountSnapshot:
        """Perform snapshot."""
        return AccountSnapshot(
            cash=MappingProxyType({"USD": self._cash.balance("USD")}),
            positions=self._positions.snapshot(),
            account_id=self._account_id,
        )

    def _apply_fill(self, message: ApplyFill) -> None:
        """Perform _apply_fill."""
        fill = message.fill
        if self._account_id is not None and fill.account_id != self._account_id:
            raise ValueError("fill account_id does not match AccountActor account_id")
        if not self._fill_ids.mark_seen(fill.fill_id):
            return
        signed_quantity = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity
        self._positions.apply_delta(fill.instrument_id, signed_quantity)
        cash_delta = (-signed_quantity * fill.price * message.multiplier) - fill.commission
        self._cash.apply_delta(message.currency, cash_delta)


__all__ = ["AccountActor", "AccountSnapshot", "ApplyFill"]
