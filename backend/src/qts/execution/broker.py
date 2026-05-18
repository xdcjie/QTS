"""Live broker execution boundary contracts.

This module intentionally remains a single cohesive boundary for all
broker-level request/adapter/report types. Splitting is unnecessary while
the surface remains stable and small.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Protocol

from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import (
    BracketLeg,
    BrokerOrderType,
    ExecutionReport,
    ExecutionReportStatus,
    OrderSide,
    OrderSpec,
    TimeInForce,
)


@dataclass(frozen=True, slots=True)
class BrokerCapabilities:
    """Broker-supported live execution features."""

    broker_id: BrokerId
    supports_market_orders: bool = True
    supports_limit_orders: bool = True
    supports_stop_orders: bool = False
    supports_cancel: bool = True
    supports_replace: bool = False
    supports_fractional: bool = False
    supports_short: bool = False
    min_order_quantity: Decimal | None = None
    lot_size: Decimal | None = None
    min_tick: Decimal | None = None
    max_order_quantity: Decimal | None = None
    supported_asset_classes: frozenset[str] = frozenset()
    supported_order_types: frozenset[BrokerOrderType] = frozenset()
    supported_time_in_force: frozenset[TimeInForce] = frozenset()

    def __post_init__(self) -> None:
        if self.min_order_quantity is not None and self.min_order_quantity <= Decimal("0"):
            raise ValueError("min_order_quantity must be positive")
        if self.lot_size is not None and self.lot_size <= Decimal("0"):
            raise ValueError("lot_size must be positive")
        if self.min_tick is not None and self.min_tick <= Decimal("0"):
            raise ValueError("min_tick must be positive")
        if self.max_order_quantity is not None and self.max_order_quantity <= Decimal("0"):
            raise ValueError("max_order_quantity must be positive")
        if any(not item.strip() for item in self.supported_asset_classes):
            raise ValueError("supported_asset_classes must not contain empty values")

    def supports_asset_class(self, asset_class: str) -> bool:
        """Perform supports_asset_class."""
        if not asset_class.strip():
            raise ValueError("asset_class must not be empty")
        return not self.supported_asset_classes or asset_class in self.supported_asset_classes

    def supports_order_type(self, order_type: BrokerOrderType) -> bool:
        """Perform supports_order_type."""
        if self.supported_order_types:
            return order_type in self.supported_order_types
        return {
            BrokerOrderType.MARKET: self.supports_market_orders,
            BrokerOrderType.LIMIT: self.supports_limit_orders,
            BrokerOrderType.STOP: self.supports_stop_orders,
            BrokerOrderType.STOP_LIMIT: self.supports_limit_orders and self.supports_stop_orders,
            BrokerOrderType.TRAILING_STOP: self.supports_stop_orders,
            BrokerOrderType.MARKET_ON_OPEN: self.supports_market_orders,
            BrokerOrderType.MARKET_ON_CLOSE: self.supports_market_orders,
            BrokerOrderType.BRACKET: self.supports_market_orders
            or self.supports_limit_orders
            or self.supports_stop_orders,
            BrokerOrderType.ICEBERG: False,
        }[order_type]

    def supports_tif(self, time_in_force: TimeInForce) -> bool:
        """Perform supports_tif."""
        return not self.supported_time_in_force or time_in_force in self.supported_time_in_force

    def validate_order_quantity(self, quantity: Decimal) -> None:
        """Validate quantity against broker size constraints."""
        if quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.min_order_quantity is not None and quantity < self.min_order_quantity:
            raise ValueError("quantity is below minimum order quantity")
        if self.max_order_quantity is not None and quantity > self.max_order_quantity:
            raise ValueError("quantity exceeds max order quantity")
        if self.lot_size is not None and quantity % self.lot_size != Decimal("0"):
            raise ValueError("quantity does not conform to broker lot size")

    def round_price(self, price: Decimal) -> Decimal:
        """Round a price to the nearest configured minimum tick."""

        if price < Decimal("0"):
            raise ValueError("price must be non-negative")
        if self.min_tick is None:
            return price
        ticks = (price / self.min_tick).to_integral_value(rounding=ROUND_HALF_UP)
        return ticks * self.min_tick

    def round_quantity(self, quantity: Decimal) -> Decimal:
        """Round a quantity down to the configured lot size."""

        if quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.lot_size is None:
            return quantity
        lots = (quantity / self.lot_size).to_integral_value(rounding=ROUND_FLOOR)
        rounded = lots * self.lot_size
        if rounded <= Decimal("0"):
            raise ValueError("quantity is below minimum broker lot size")
        return rounded

    def to_manifest_payload(self) -> dict[str, object]:
        """Serialize auditable broker capability assumptions."""
        return {
            "broker_id": self.broker_id.value,
            "supports_market_orders": self.supports_market_orders,
            "supports_limit_orders": self.supports_limit_orders,
            "supports_stop_orders": self.supports_stop_orders,
            "supports_cancel": self.supports_cancel,
            "supports_replace": self.supports_replace,
            "supports_fractional": self.supports_fractional,
            "supports_short": self.supports_short,
            "min_order_quantity": (
                str(self.min_order_quantity) if self.min_order_quantity is not None else None
            ),
            "lot_size": str(self.lot_size) if self.lot_size is not None else None,
            "min_tick": str(self.min_tick) if self.min_tick is not None else None,
            "max_order_quantity": (
                str(self.max_order_quantity) if self.max_order_quantity is not None else None
            ),
            "supported_asset_classes": sorted(self.supported_asset_classes),
            "supported_order_types": sorted(
                order_type.value for order_type in self.supported_order_types
            ),
            "supported_time_in_force": sorted(
                time_in_force.value for time_in_force in self.supported_time_in_force
            ),
        }


@dataclass(frozen=True, slots=True)
class BrokerOrderRequest:
    """Internal order request sent to the broker adapter boundary."""

    order_id: OrderId
    client_order_id: str
    account_id: AccountId
    strategy_id: StrategyId | None
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    order_type: BrokerOrderType = BrokerOrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.DAY
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    trail_amount: Decimal | None = None
    trail_percent: Decimal | None = None
    good_til_date: datetime | None = None
    bracket_legs: tuple[BracketLeg, ...] | None = None

    def __post_init__(self) -> None:
        if not self.client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")

        _ = self.order_spec

    @property
    def order_spec(self) -> OrderSpec:
        """Return the request fields as a single execution specification."""
        from qts.domain.orders import BracketSpec

        return OrderSpec(
            order_type=self.order_type,
            time_in_force=self.time_in_force,
            limit_price=self.limit_price,
            stop_price=self.stop_price,
            trail_amount=self.trail_amount,
            trail_percent=self.trail_percent,
            good_til_date=self.good_til_date if self.good_til_date is not None else None,
            bracket=None if self.bracket_legs is None else BracketSpec(self.bracket_legs),
        )


class BrokerExecutionReportStatus(StrEnum):
    """Broker-boundary execution report status."""

    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class BrokerExecutionReport:
    """Normalized broker callback before it reaches OrderManager."""

    report_id: str
    broker_id: BrokerId
    broker_order_id: str
    order_id: OrderId
    account_id: AccountId
    strategy_id: StrategyId | None
    instrument_id: InstrumentId
    status: BrokerExecutionReportStatus
    filled_quantity: Decimal = Decimal("0")
    fill_price: Decimal | None = None
    fill_id: str | None = None
    fill_time: datetime | None = None

    def __post_init__(self) -> None:
        if not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if self.filled_quantity < Decimal("0"):
            raise ValueError("filled_quantity must be non-negative")
        if self.filled_quantity > Decimal("0") and self.fill_price is None:
            raise ValueError("fill_price is required for fills")


class BrokerAdapter(Protocol):
    """Stable broker execution boundary."""

    @property
    def capabilities(self) -> BrokerCapabilities:
        """Return broker capabilities."""
        ...

    def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport:
        """Submit an order request."""
        ...

    def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport:
        """Cancel an order by internal ID."""
        ...


def normalize_broker_status(status: BrokerExecutionReportStatus) -> ExecutionReportStatus:
    """Map broker status to normalized execution status."""

    return ExecutionReportStatus(status.value)


def normalize_broker_execution_report(report: BrokerExecutionReport) -> ExecutionReport:
    """Convert broker-boundary report into the OrderManager report type."""

    return ExecutionReport(
        report_id=report.report_id,
        broker_order_id=report.broker_order_id,
        status=normalize_broker_status(report.status),
        filled_quantity=report.filled_quantity,
        fill_price=report.fill_price,
        fill_id=report.fill_id,
        fill_time=report.fill_time,
    )


__all__ = [
    "BrokerAdapter",
    "BrokerCapabilities",
    "BrokerExecutionReport",
    "BrokerExecutionReportStatus",
    "BrokerOrderType",
    "BrokerOrderRequest",
    "TimeInForce",
    "normalize_broker_status",
    "normalize_broker_execution_report",
]
