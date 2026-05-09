"""API-facing service interfaces."""

from __future__ import annotations

from typing import Protocol


class AccountService(Protocol):
    def snapshot(self, account_id: str) -> object: ...


class OrderService(Protocol):
    def status(self, order_id: str) -> object: ...


class RiskService(Protocol):
    def rules(self, account_id: str) -> object: ...


__all__ = ["AccountService", "OrderService", "RiskService"]
