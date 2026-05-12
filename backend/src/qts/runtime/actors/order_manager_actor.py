"""OrderManager actor MVP."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId, OrderId
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import ExecutionReport, Order, OrderFill, OrderIntent, OrderManager
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

    def __init__(
        self,
        *,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None = None,
    ) -> None:
        self._manager = OrderManager()
        self._execution_ref = execution_ref
        self._account_ref = account_ref
        self._multiplier_by_instrument = dict(multiplier_by_instrument or {})
        self._fills: list[OrderFill] = []

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

    @property
    def fills(self) -> tuple[OrderFill, ...]:
        return tuple(self._fills)

    @property
    def fill_count(self) -> int:
        return len(self._fills)

    def fills_since(self, index: int) -> tuple[OrderFill, ...]:
        return tuple(self._fills[index:])

    def compact_for_streaming(self, order_ids: Iterable[OrderId]) -> None:
        for order_id in order_ids:
            self._manager.discard_terminal_order(order_id)
        self._fills.clear()

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
            self._fills.append(fill)
            self._account_ref.tell(
                ApplyFill(
                    fill=fill,
                    currency="USD",
                    multiplier=self._multiplier_by_instrument.get(fill.instrument_id, Decimal("1")),
                )
            )


__all__ = ["OrderManagerActor", "SubmitOrder"]
