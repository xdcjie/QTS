"""Cash balance book."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qts.portfolio.reservation_book import ReservationBook


class CashBook:
    """Mutable cash balance book owned by AccountActor for account-state mutation."""

    def __init__(self, balances: Mapping[str, Decimal] | None = None) -> None:
        """Seed the book with an optional mapping of starting currency balances."""
        self._balances = dict(balances or {})

    def apply_delta(self, currency: str, amount_delta: Decimal) -> None:
        """Adjust a currency balance by a signed delta."""
        normalized = self._normalize_currency(currency)
        self._balances[normalized] = self.balance(normalized) + amount_delta

    def balance(self, currency: str) -> Decimal:
        """Return the balance for a currency, defaulting to zero."""
        return self._balances.get(self._normalize_currency(currency), Decimal("0"))

    def balances(self) -> dict[str, Decimal]:
        """Return a copy of all currency balances for multi-currency snapshotting."""
        return dict(self._balances)

    def available(self, currency: str, *, reservations: ReservationBook) -> Decimal:
        """Return the balance net of reserved funds for a currency."""
        normalized = self._normalize_currency(currency)
        return self.balance(normalized) - reservations.reserved(normalized)

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        """Return the trimmed, upper-cased currency code, rejecting empty input."""
        normalized = currency.strip().upper()
        if not normalized:
            raise ValueError("currency must not be empty")
        return normalized


__all__ = ["CashBook"]
