"""Control-plane DTOs for strategy, order, and account query routes.

These are stable public projections returned by the strategy-control,
order-query, and account-query application services. They carry no runtime,
actor, or broker types so the API layer can map them to response schemas
without importing internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StrategyStatusDTO:
    """Stable strategy lifecycle status projection."""

    strategy_id: str
    status: str

    def __post_init__(self) -> None:
        """Validate strategy status fields."""
        if not self.strategy_id.strip():
            raise ValueError("strategy_id must not be empty")
        if not self.status.strip():
            raise ValueError("status must not be empty")


@dataclass(frozen=True, slots=True)
class OrderStatusDTO:
    """Stable order lifecycle status projection."""

    order_id: str
    status: str

    def __post_init__(self) -> None:
        """Validate order status fields."""
        if not self.order_id.strip():
            raise ValueError("order_id must not be empty")
        if not self.status.strip():
            raise ValueError("status must not be empty")


@dataclass(frozen=True, slots=True)
class AccountSnapshotDTO:
    """Stable account snapshot projection with per-currency cash balances."""

    account_id: str
    cash: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate account snapshot fields and freeze cash balances."""
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        object.__setattr__(self, "cash", dict(self.cash))


__all__ = [
    "AccountSnapshotDTO",
    "OrderStatusDTO",
    "StrategyStatusDTO",
]
