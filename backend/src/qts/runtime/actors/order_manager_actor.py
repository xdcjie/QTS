"""OrderManager actor MVP."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import OrderId
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import ExecutionReport, Order, OrderIntent, OrderManager
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import ApplyFill
from qts.runtime.actors.execution_actor import OrderExecutionRequest


@dataclass(frozen=True, slots=True)
class SubmitOrder:
    """Message to submit an approved order to an execution actor."""

    intent: OrderIntent
    risk_decision: RiskDecision
    broker_order_id: str
    market_price: Decimal


class OrderManagerActor(Actor):
    """Actor-owned OrderManager wrapper."""

    def __init__(self, *, execution_ref: ActorRef, account_ref: ActorRef) -> None:
        self._manager = OrderManager()
        self._execution_ref = execution_ref
        self._account_ref = account_ref

    def handle(self, message: object) -> None:
        if isinstance(message, SubmitOrder):
            self._handle_submit(message)
            return
        if isinstance(message, ExecutionReport):
            self._handle_report(message)
            return
        raise TypeError(f"unsupported order manager message: {type(message).__name__}")

    def get_order(self, order_id: OrderId) -> Order:
        return self._manager.get_order(order_id)

    def _handle_submit(self, message: SubmitOrder) -> None:
        order = self._manager.create_order(message.intent, risk_decision=message.risk_decision)
        self._manager.mark_sent(order.order_id, broker_order_id=message.broker_order_id)
        self._execution_ref.tell(
            OrderExecutionRequest(
                intent=message.intent,
                broker_order_id=message.broker_order_id,
                market_price=message.market_price,
            )
        )

    def _handle_report(self, message: ExecutionReport) -> None:
        result = self._manager.process_report(message)
        for fill in result.fills:
            self._account_ref.tell(ApplyFill(fill=fill, currency="USD", multiplier=Decimal("1")))


__all__ = ["OrderManagerActor", "SubmitOrder"]
