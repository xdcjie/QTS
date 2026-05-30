"""Cash reservation book."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import OrderId


@dataclass(frozen=True, slots=True)
class Reservation:
    """Cash reservation by order ID."""

    reservation_id: OrderId
    currency: str
    amount: Decimal


class ReservationBook:
    """Idempotent cash reservations keyed by order ID."""

    def __init__(self) -> None:
        """Initialize an empty reservation map keyed by order ID."""
        self._reservations: dict[OrderId, Reservation] = {}

    def reserve(self, reservation_id: OrderId, currency: str, amount: Decimal) -> None:
        """Record a non-negative cash reservation, ignoring duplicate order IDs."""
        if amount < Decimal("0"):
            raise ValueError("amount must be non-negative")
        if reservation_id in self._reservations:
            return
        normalized = self._normalize_currency(currency)
        self._reservations[reservation_id] = Reservation(
            reservation_id=reservation_id,
            currency=normalized,
            amount=amount,
        )

    def release(self, reservation_id: OrderId) -> None:
        """Drop the reservation for an order ID if one exists."""
        self._reservations.pop(reservation_id, None)

    def reserved(self, currency: str) -> Decimal:
        """Return the total amount currently reserved in the given currency."""
        normalized = self._normalize_currency(currency)
        return sum(
            (
                reservation.amount
                for reservation in self._reservations.values()
                if reservation.currency == normalized
            ),
            Decimal("0"),
        )

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        """Return the currency code trimmed and uppercased, raising if empty."""
        normalized = currency.strip().upper()
        if not normalized:
            raise ValueError("currency must not be empty")
        return normalized


__all__ = ["Reservation", "ReservationBook"]
