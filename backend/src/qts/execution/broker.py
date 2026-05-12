"""Live broker execution boundary contracts and fake adapter.

This module intentionally remains a single cohesive boundary for all broker-level
request/adapter/report types. Splitting is unnecessary while the surface remains
stable and small.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderSide


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
    max_order_quantity: Decimal | None = None
    supported_asset_classes: frozenset[str] = frozenset()
    supported_order_types: frozenset[BrokerOrderType] = frozenset()
    supported_time_in_force: frozenset[TimeInForce] = frozenset()

    def __post_init__(self) -> None:
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
        }[order_type]

    def supports_tif(self, time_in_force: TimeInForce) -> bool:
        """Perform supports_tif."""
        return not self.supported_time_in_force or time_in_force in self.supported_time_in_force


class BrokerOrderType(StrEnum):
    """Order types modeled before broker submission."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class TimeInForce(StrEnum):
    """Time-in-force values modeled at the execution boundary."""

    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"


@dataclass(frozen=True, slots=True)
class BrokerOrderRequest:
    """Internal order request sent to the broker adapter boundary."""

    order_id: OrderId
    account_id: AccountId
    strategy_id: StrategyId | None
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")


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


class FakeBrokerAdapter:
    """Deterministic fake broker for live-beta tests and local runs."""

    def __init__(self, *, broker_id: BrokerId) -> None:
        self._broker_id = broker_id
        self._orders: dict[OrderId, BrokerOrderRequest] = {}
        self._broker_order_ids: dict[OrderId, str] = {}
        self._sequence = 0

    @property
    def capabilities(self) -> BrokerCapabilities:
        """Perform capabilities."""
        return BrokerCapabilities(broker_id=self._broker_id)

    def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport:
        """Perform submit_order."""
        self._orders[request.order_id] = request
        broker_order_id = self._broker_order_ids.setdefault(
            request.order_id, f"{self._broker_id.value}-{len(self._broker_order_ids) + 1}"
        )
        return self._report(
            request,
            broker_order_id=broker_order_id,
            status=BrokerExecutionReportStatus.ACCEPTED,
        )

    def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport:
        """Perform cancel_order."""
        request = self._orders[order_id]
        return self._report(
            request,
            broker_order_id=self._broker_order_ids[order_id],
            status=BrokerExecutionReportStatus.CANCELLED,
        )

    def emit_fill(
        self,
        *,
        order_id: OrderId,
        quantity: Decimal,
        price: Decimal,
        fill_id: str,
    ) -> BrokerExecutionReport:
        """Perform emit_fill."""
        if quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if price < Decimal("0"):
            raise ValueError("price must be non-negative")
        if not fill_id.strip():
            raise ValueError("fill_id must not be empty")
        request = self._orders[order_id]
        status = (
            BrokerExecutionReportStatus.FILLED
            if quantity >= request.quantity
            else BrokerExecutionReportStatus.PARTIALLY_FILLED
        )
        return self._report(
            request,
            broker_order_id=self._broker_order_ids[order_id],
            status=status,
            filled_quantity=quantity,
            fill_price=price,
            fill_id=fill_id,
        )

    def _report(
        self,
        request: BrokerOrderRequest,
        *,
        broker_order_id: str,
        status: BrokerExecutionReportStatus,
        filled_quantity: Decimal = Decimal("0"),
        fill_price: Decimal | None = None,
        fill_id: str | None = None,
    ) -> BrokerExecutionReport:
        self._sequence += 1
        return BrokerExecutionReport(
            report_id=f"{self._broker_id.value}-report-{self._sequence}",
            broker_id=self._broker_id,
            broker_order_id=broker_order_id,
            order_id=request.order_id,
            account_id=request.account_id,
            strategy_id=request.strategy_id,
            instrument_id=request.instrument_id,
            status=status,
            filled_quantity=filled_quantity,
            fill_price=fill_price,
            fill_id=fill_id,
        )


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
    )


__all__ = [
    "BrokerAdapter",
    "BrokerCapabilities",
    "BrokerExecutionReport",
    "BrokerExecutionReportStatus",
    "BrokerOrderType",
    "BrokerOrderRequest",
    "FakeBrokerAdapter",
    "TimeInForce",
    "normalize_broker_status",
    "normalize_broker_execution_report",
]
