"""Account actor MVP."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType

from qts.core.ids import AccountId
from qts.domain.orders import OrderFill, OrderSide
from qts.execution.idempotency import FillIdempotencyStore
from qts.portfolio.account_snapshot import AccountSnapshot
from qts.portfolio.cash_book import CashBook
from qts.portfolio.holdings import HoldingBook, PositionClosed
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorUnhandledMessageError


@dataclass(frozen=True, slots=True)
class GetAccountSnapshot:
    """Ask the AccountActor for its current snapshot."""

    def validate_response(self, response: object) -> AccountSnapshot:
        """Return a typed account snapshot response."""
        if not isinstance(response, AccountSnapshot):
            raise TypeError("expected AccountSnapshot response")
        return response


@dataclass(frozen=True, slots=True)
class DrainPositionClosedEvents:
    """Ask the AccountActor to drain and return buffered PositionClosed events."""

    def validate_response(self, response: object) -> tuple[PositionClosed, ...]:
        """Return typed position-closed events."""
        if not isinstance(response, tuple) or not all(
            isinstance(event, PositionClosed) for event in response
        ):
            raise TypeError("expected PositionClosed event tuple response")
        return response


@dataclass(frozen=True, slots=True)
class ApplyFill:
    """Message instructing AccountActor to apply a validated fill."""

    fill: OrderFill
    currency: str
    multiplier: Decimal
    fill_time: datetime | None = None


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
        self._holdings = HoldingBook()
        self._fill_ids = FillIdempotencyStore()
        self._position_closed_events: list[PositionClosed] = []

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, tuple) and len(message) == 2:
            query, response_mailbox = message
            if isinstance(query, GetAccountSnapshot):
                response_mailbox.put(self.snapshot())
                return
            if isinstance(query, DrainPositionClosedEvents):
                response_mailbox.put(self.drain_position_closed_events())
                return
        if isinstance(message, ApplyFill):
            self._apply_fill(message)
            return
        raise ActorUnhandledMessageError(f"unsupported account message: {type(message).__name__}")

    def snapshot(self) -> AccountSnapshot:
        """Return current account snapshot."""
        return AccountSnapshot(
            cash=MappingProxyType({"USD": self._cash.balance("USD")}),
            holdings=self._holdings.snapshot(),
            account_id=self._account_id,
            seen_fill_ids=self._fill_ids.snapshot(),
        )

    @classmethod
    def restore(cls, snapshot: AccountSnapshot) -> AccountActor:
        """Restore account-owned state from an actor snapshot."""
        actor = cls(initial_cash=snapshot.cash, account_id=snapshot.account_id)
        actor._holdings = HoldingBook.restore(snapshot.holdings)
        actor._fill_ids = FillIdempotencyStore.restore(snapshot.seen_fill_ids)
        return actor

    def drain_position_closed_events(self) -> tuple[PositionClosed, ...]:
        """Return and clear the buffered PositionClosed events.

        The runtime market-data coordinator calls this after every dispatch
        tick to emit ``account.position_closed`` events through the shared
        sink, keeping Holdings and the report artifacts in single-source-of-
        truth agreement on realized PnL.
        """
        events = tuple(self._position_closed_events)
        self._position_closed_events.clear()
        return events

    def _apply_fill(self, message: ApplyFill) -> None:
        """Perform _apply_fill."""
        fill = message.fill
        if self._account_id is not None and fill.account_id != self._account_id:
            raise ValueError("fill account_id does not match AccountActor account_id")
        if not self._fill_ids.mark_seen(fill.fill_id):
            return
        signed_quantity = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity
        self._position_closed_events.extend(
            self._holdings.apply_fill(
                instrument_id=fill.instrument_id,
                signed_quantity=signed_quantity,
                price=fill.price,
                multiplier=message.multiplier,
                fill_time=message.fill_time,
            )
        )
        cash_delta = (-signed_quantity * fill.price * message.multiplier) - fill.commission
        self._cash.apply_delta(message.currency, cash_delta)


__all__ = [
    "AccountActor",
    "AccountSnapshot",
    "ApplyFill",
    "DrainPositionClosedEvents",
    "GetAccountSnapshot",
]
