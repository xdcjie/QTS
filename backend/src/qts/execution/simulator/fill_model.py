"""Deterministic simulated fill model.

Only ``ImmediateFillModel`` is retained: the simulated execution adapter
computes its own bar-touch fill semantics in
``SimulatedExecutionAdapter._evaluate_fill`` (OPT-27.1) and only consults
``ImmediateFillModel`` for the manifest assumptions payload.
"""

from __future__ import annotations

from decimal import Decimal

from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent


class ImmediateFillModel:
    """Fills market orders at the provided market price."""

    model_name = "immediate_market_fill"
    model_version = "1"

    def to_manifest_payload(self) -> dict[str, object]:
        """Serialize fill-model assumptions for run manifests."""
        return {
            "fill_model_name": self.model_name,
            "fill_model_version": self.model_version,
            "volume_participation_limit": None,
            "partial_fill_policy": "none",
        }

    def fill(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        """Fill at the supplied market price."""
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
