"""Operational dashboard snapshot schema."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RuntimeSubscriptionSnapshot:
    """One runtime market-data subscription row."""

    subscription_id: str
    instrument_id: str
    requested_timeframe: str
    source_id: str
    status: str

    def to_schema(self) -> dict[str, str]:
        """Serialize this subscription row."""
        return {
            "subscription_id": self.subscription_id,
            "instrument_id": self.instrument_id,
            "requested_timeframe": self.requested_timeframe,
            "source_id": self.source_id,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class OpenOrderSnapshot:
    """One open order row."""

    order_id: str
    account_id: str
    instrument_id: str
    status: str

    def to_schema(self) -> dict[str, str]:
        """Serialize this open order row."""
        return {
            "order_id": self.order_id,
            "account_id": self.account_id,
            "instrument_id": self.instrument_id,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    """One account position row."""

    account_id: str
    instrument_id: str
    quantity: Decimal

    def to_schema(self) -> dict[str, str]:
        """Serialize this position row."""
        return {
            "account_id": self.account_id,
            "instrument_id": self.instrument_id,
            "quantity": str(self.quantity),
        }


@dataclass(frozen=True, slots=True)
class CashSnapshot:
    """One account cash balance row."""

    account_id: str
    currency: str
    balance: Decimal

    def to_schema(self) -> dict[str, str]:
        """Serialize this cash row."""
        return {
            "account_id": self.account_id,
            "currency": self.currency,
            "balance": str(self.balance),
        }


@dataclass(frozen=True, slots=True)
class RiskStatusSnapshot:
    """Current runtime risk status."""

    status: str
    kill_switch_active: bool

    def to_schema(self) -> dict[str, str | bool]:
        """Serialize the risk status."""
        return {
            "status": self.status,
            "kill_switch_active": self.kill_switch_active,
        }


@dataclass(frozen=True, slots=True)
class BrokerConnectionSnapshot:
    """Current broker connection status."""

    status: str
    broker_id: str

    def to_schema(self) -> dict[str, str]:
        """Serialize the broker connection status."""
        return {
            "status": self.status,
            "broker_id": self.broker_id,
        }


@dataclass(frozen=True, slots=True)
class OperationalDashboardSnapshot:
    """Runtime state snapshot for operational dashboards."""

    runtime_state: str
    subscriptions: tuple[RuntimeSubscriptionSnapshot, ...]
    open_orders: tuple[OpenOrderSnapshot, ...]
    positions: tuple[PositionSnapshot, ...]
    cash: tuple[CashSnapshot, ...]
    risk: RiskStatusSnapshot
    broker_connection: BrokerConnectionSnapshot
    reconciliation_status: str

    def to_schema(self) -> dict[str, object]:
        """Serialize the complete operational dashboard schema."""
        return {
            "runtime_state": self.runtime_state,
            "subscriptions": [row.to_schema() for row in self.subscriptions],
            "open_orders": [row.to_schema() for row in self.open_orders],
            "positions": [row.to_schema() for row in self.positions],
            "cash": [row.to_schema() for row in self.cash],
            "risk": self.risk.to_schema(),
            "broker_connection": self.broker_connection.to_schema(),
            "reconciliation_status": self.reconciliation_status,
        }


__all__ = [
    "BrokerConnectionSnapshot",
    "CashSnapshot",
    "OpenOrderSnapshot",
    "OperationalDashboardSnapshot",
    "PositionSnapshot",
    "RiskStatusSnapshot",
    "RuntimeSubscriptionSnapshot",
]
