"""Cash balance book."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qts.portfolio.reservation_book import ReservationBook


class CashBook:
    """Mutable cash balance book intended to be owned by AccountActor later."""

    def __init__(self, balances: Mapping[str, Decimal] | None = None) -> None:
        self._balances = dict(balances or {})

    def apply_delta(self, currency: str, amount_delta: Decimal) -> None:
        normalized = self._normalize_currency(currency)
        self._balances[normalized] = self.balance(normalized) + amount_delta

    def balance(self, currency: str) -> Decimal:
        return self._balances.get(self._normalize_currency(currency), Decimal("0"))

    def available(self, currency: str, *, reservations: ReservationBook) -> Decimal:
        normalized = self._normalize_currency(currency)
        return self.balance(normalized) - reservations.reserved(normalized)

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        normalized = currency.strip().upper()
        if not normalized:
            raise ValueError("currency must not be empty")
        return normalized


__all__ = ["CashBook"]
