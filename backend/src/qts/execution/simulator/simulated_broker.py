"""Deterministic simulated broker."""

from __future__ import annotations

from decimal import Decimal

from qts.execution.order_manager import ExecutionReport, OrderIntent
from qts.execution.simulator.fill_model import ImmediateFillModel


class SimulatedBroker:
    """Broker simulator with no external dependency."""

    def __init__(self, fill_model: ImmediateFillModel | None = None) -> None:
        self._fill_model = fill_model or ImmediateFillModel()

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        return self._fill_model.fill(
            intent,
            broker_order_id=broker_order_id,
            market_price=market_price,
        )


__all__ = ["SimulatedBroker"]
