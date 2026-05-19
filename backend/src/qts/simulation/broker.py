"""Production-side simulated broker adapter."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import BrokerId, OrderId
from qts.domain.orders import ExecutionReportStatus
from qts.execution.broker import (
    BrokerCapabilities,
    BrokerExecutionReport,
    BrokerOrderRequest,
)


class SimulatedBrokerAdapter:
    """Deterministic simulated broker adapter for non-test runtime paths."""

    def __init__(self, *, broker_id: BrokerId | None = None) -> None:
        self._broker_id = broker_id or BrokerId("simulated")
        self._orders: dict[OrderId, BrokerOrderRequest] = {}
        self._broker_order_ids: dict[OrderId, str] = {}
        self._sequence = 0

    @property
    def capabilities(self) -> BrokerCapabilities:
        """Return deterministic broker capabilities."""
        return BrokerCapabilities(broker_id=self._broker_id)

    def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport:
        """Submit an order and record it as accepted."""
        self._orders[request.order_id] = request
        broker_order_id = self._broker_order_ids.setdefault(
            request.order_id,
            f"{self._broker_id.value}-{len(self._broker_order_ids) + 1}",
        )
        return self._report(
            request,
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
        )

    def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport:
        """Cancel a previously accepted order."""
        request = self._orders[order_id]
        return self._report(
            request,
            broker_order_id=self._broker_order_ids[order_id],
            status=ExecutionReportStatus.CANCELLED,
        )

    def order_request(self, order_id: OrderId) -> BrokerOrderRequest:
        """Return a previously submitted order request."""
        return self._orders[order_id]

    def emit_fill(
        self,
        *,
        order_id: OrderId,
        quantity: Decimal,
        price: Decimal,
        fill_id: str,
    ) -> BrokerExecutionReport:
        """Emit a deterministic fill for an existing order."""
        if quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if price < Decimal("0"):
            raise ValueError("price must be non-negative")
        if not fill_id.strip():
            raise ValueError("fill_id must not be empty")
        request = self.order_request(order_id)
        status = (
            ExecutionReportStatus.FILLED
            if quantity >= request.quantity
            else ExecutionReportStatus.PARTIALLY_FILLED
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
        status: ExecutionReportStatus,
        filled_quantity: Decimal = Decimal("0"),
        fill_price: Decimal | None = None,
        fill_id: str | None = None,
    ) -> BrokerExecutionReport:
        """Build a normalized broker execution report."""
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


__all__ = ["SimulatedBrokerAdapter"]
