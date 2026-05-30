"""Public API schemas for accounts, orders, risk, and strategies."""

from __future__ import annotations

from pydantic import BaseModel


class StrategyStatusSchema(BaseModel):
    """Strategy status response schema."""

    strategy_id: str
    status: str


class AccountSnapshotSchema(BaseModel):
    """Account snapshot response schema."""

    account_id: str
    cash: dict[str, str]


class OrderStatusSchema(BaseModel):
    """Order status response schema."""

    order_id: str
    status: str


class RiskRuleSchema(BaseModel):
    """Risk rule response schema."""

    rule_id: str
    name: str


class OperationalErrorSchema(BaseModel):
    """Operational error response schema."""

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
        """Build an error schema from a code and message, hiding exception detail."""
        del exc
        return cls(code=code, message=message, detail=None)


__all__ = [
    "AccountSnapshotSchema",
    "OperationalErrorSchema",
    "OrderStatusSchema",
    "RiskRuleSchema",
    "StrategyStatusSchema",
]
