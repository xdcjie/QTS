"""Account actor MVP."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from qts.core.ids import InstrumentId
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


class AccountActor(Actor):
    """Owns account cash and position state."""

    def __init__(self, initial_cash: Mapping[str, Decimal] | None = None) -> None:
        self._cash = CashBook(initial_cash)
        self._positions = PositionBook()
        self._fill_ids = FillIdempotencyStore()

    def handle(self, message: object) -> None:
        if isinstance(message, ApplyFill):
            self._apply_fill(message)
            return
        raise TypeError(f"unsupported account message: {type(message).__name__}")

    def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            cash=MappingProxyType({"USD": self._cash.balance("USD")}),
            positions=self._positions.snapshot(),
        )

    def _apply_fill(self, message: ApplyFill) -> None:
        fill = message.fill
        if not self._fill_ids.mark_seen(fill.fill_id):
            return
        signed_quantity = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity
        self._positions.apply_delta(fill.instrument_id, signed_quantity)
        cash_delta = -signed_quantity * fill.price * message.multiplier
        self._cash.apply_delta(message.currency, cash_delta)


__all__ = ["AccountActor", "AccountSnapshot", "ApplyFill"]
