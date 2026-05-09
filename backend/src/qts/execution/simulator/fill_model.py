"""Deterministic simulated fill model."""

from __future__ import annotations

from decimal import Decimal

from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus, OrderIntent


class ImmediateFillModel:
    """Fills market orders at the provided market price."""

    def fill(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill-1",
        )


__all__ = ["ImmediateFillModel"]
