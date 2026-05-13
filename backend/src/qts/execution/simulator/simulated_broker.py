"""Deterministic simulated broker."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import OrderId
from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus, OrderIntent
from qts.execution.simulator.fill_model import ImmediateFillModel


class SimulatedBroker:
    """Broker simulator with no external dependency."""

    def __init__(self, fill_model: ImmediateFillModel | None = None) -> None:
        """Perform __init__."""
        self._fill_model = fill_model or ImmediateFillModel()

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        """Perform execute_market_order."""
        return self._fill_model.fill(
            intent,
            broker_order_id=broker_order_id,
            market_price=market_price,
        )

    def cancel_order(self, order_id: OrderId, *, broker_order_id: str) -> ExecutionReport:
        """Return a deterministic cancellation report."""
        _ = order_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancel-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


__all__ = ["SimulatedBroker"]
