"""API-facing service interfaces."""

from __future__ import annotations

from typing import Protocol


class AccountService(Protocol):
    """Account query service boundary."""

    def snapshot(self, account_id: str) -> object:
        """Return an account snapshot."""
        ...


class OrderService(Protocol):
    """Order query service boundary."""

    def status(self, order_id: str) -> object:
        """Return order status."""
        ...


class RiskService(Protocol):
    """Risk query service boundary."""

    def rules(self, account_id: str) -> object:
        """Return configured risk rules."""
        ...


__all__ = ["AccountService", "OrderService", "RiskService"]
