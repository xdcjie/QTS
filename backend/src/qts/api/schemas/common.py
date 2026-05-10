"""Public API schemas for accounts, orders, risk, and strategies."""

from __future__ import annotations

from pydantic import BaseModel


class StrategyStatusSchema(BaseModel):
    strategy_id: str
    status: str


class AccountSnapshotSchema(BaseModel):
    account_id: str
    cash: dict[str, str]


class OrderStatusSchema(BaseModel):
    order_id: str
    status: str


class RiskRuleSchema(BaseModel):
    rule_id: str
    name: str


class OperationalErrorSchema(BaseModel):
    code: str
    message: str
    detail: str | None = None

    @classmethod
    def from_exception(
        cls,
        *,
        code: str,
        message: str,
        exc: Exception,
    ) -> OperationalErrorSchema:
        del exc
        return cls(code=code, message=message, detail=None)


__all__ = [
    "AccountSnapshotSchema",
    "OperationalErrorSchema",
    "OrderStatusSchema",
    "RiskRuleSchema",
    "StrategyStatusSchema",
]
