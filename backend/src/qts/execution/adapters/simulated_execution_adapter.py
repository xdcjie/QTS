"""Execution adapter that applies backtest fill-cost assumptions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from qts.core.ids import OrderId
from qts.domain.orders import OrderSide
from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus, OrderIntent


class SimulatedExecutionCostModel(Protocol):
    """Cost-model fields required by simulated execution."""

    @property
    def fixed_commission_per_contract(self) -> Decimal:
        """Fixed commission charged per filled unit."""
        ...

    @property
    def slippage_bps(self) -> Decimal:
        """Slippage applied to simulated market fills."""
        ...


@dataclass(frozen=True, slots=True)
class SimulatedExecutionAdapter:
    """Apply deterministic commission and slippage assumptions for backtests."""

    cost_model: SimulatedExecutionCostModel

    def __post_init__(self) -> None:
        """Validate and normalize cost-model-backed configuration."""
        if self.cost_model is None:
            raise ValueError("cost_model is required")

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        """Execute a market order with cost-model adjustments."""
        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        slippage = market_price * self.cost_model.slippage_bps / Decimal("10000")
        fill_price = (
            market_price + slippage if intent.side is OrderSide.BUY else market_price - slippage
        )
        commission = self.cost_model.fixed_commission_per_contract * intent.quantity
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=fill_price,
            fill_id=f"{broker_order_id}-fill-1",
            commission=commission,
            slippage=abs(fill_price - market_price),
        )

    def cancel_order(self, order_id: OrderId, *, broker_order_id: str) -> ExecutionReport:
        """Return a deterministic cancellation report for actor parity."""
        _ = order_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancel-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


__all__ = ["SimulatedExecutionAdapter", "SimulatedExecutionCostModel"]
