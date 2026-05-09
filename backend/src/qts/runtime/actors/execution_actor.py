"""Order execution actor MVP."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from qts.execution.order_manager import ExecutionReport, OrderIntent
from qts.execution.simulator.simulated_broker import SimulatedBroker
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef


class ExecutionAdapter(Protocol):
    """Execution boundary contract used by the actor."""

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport: ...


@dataclass(frozen=True, slots=True)
class OrderExecutionRequest:
    """Message requesting order execution."""

    intent: OrderIntent
    broker_order_id: str
    market_price: Decimal


class ExecutionActor(Actor):
    """Actor wrapper for an order execution adapter or simulator."""

    def __init__(
        self,
        *,
        order_manager_ref: ActorRef,
        execution_adapter: ExecutionAdapter | None = None,
    ) -> None:
        self._order_manager_ref = order_manager_ref
        self._execution_adapter = execution_adapter or SimulatedBroker()

    def handle(self, message: object) -> None:
        if isinstance(message, OrderExecutionRequest):
            report = self._execution_adapter.execute_market_order(
                message.intent,
                broker_order_id=message.broker_order_id,
                market_price=message.market_price,
            )
            self._order_manager_ref.tell(report)
            return
        raise TypeError(f"unsupported execution message: {type(message).__name__}")


__all__ = ["ExecutionActor", "OrderExecutionRequest"]
