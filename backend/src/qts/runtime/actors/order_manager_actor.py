"""OrderManager actor MVP."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import CancelIntent
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import ExecutionReport, Order, OrderFill, OrderIntent, OrderManager
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.execution_actor import OrderCancelRequest, OrderExecutionRequest
from qts.runtime.execution_report_handler import ExecutionReportHandler


@dataclass(frozen=True, slots=True)
class SubmitOrder:
    """Message to submit an approved order to an execution actor."""

    intent: OrderIntent
    risk_decision: RiskDecision
    broker_order_id: str
    market_price: Decimal


@dataclass(frozen=True, slots=True)
class CancelOrder:
    """Message to cancel an active order through the execution actor."""

    intent: CancelIntent


class OrderManagerActor(Actor):
    """Actor-owned OrderManager wrapper."""

    def __init__(
        self,
        *,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None = None,
    ) -> None:
        """Perform __init__."""
        self._manager = OrderManager()
        self._execution_ref = execution_ref
        self._execution_report_handler = ExecutionReportHandler(
            order_manager=self._manager,
            account_ref=account_ref,
            multiplier_by_instrument=multiplier_by_instrument,
        )
        self._fills: list[OrderFill] = []

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, SubmitOrder):
            self._handle_submit(message)
            return
        if isinstance(message, CancelOrder):
            self._handle_cancel(message)
            return
        if isinstance(message, ExecutionReport):
            self._handle_report(message)
            return
        raise TypeError(f"unsupported order manager message: {type(message).__name__}")

    def get_order(self, order_id: OrderId) -> Order:
        """Perform get_order."""
        return self._manager.get_order(order_id)

    @property
    def fills(self) -> tuple[OrderFill, ...]:
        """Perform fills."""
        return tuple(self._fills)

    @property
    def fill_count(self) -> int:
        """Perform fill_count."""
        return len(self._fills)

    def fills_since(self, index: int) -> tuple[OrderFill, ...]:
        """Perform fills_since."""
        return tuple(self._fills[index:])

    def compact_for_streaming(self, order_ids: Iterable[OrderId]) -> None:
        """Perform compact_for_streaming."""
        for order_id in order_ids:
            self._manager.discard_terminal_order(order_id)
        self._fills.clear()

    def _handle_submit(self, message: SubmitOrder) -> None:
        """Perform _handle_submit."""
        order = self._manager.create_order(message.intent, risk_decision=message.risk_decision)
        self._manager.mark_sent(order.order_id, broker_order_id=message.broker_order_id)
        self._execution_ref.tell(
            OrderExecutionRequest(
                intent=message.intent,
                broker_order_id=message.broker_order_id,
                market_price=message.market_price,
            )
        )

    def _handle_cancel(self, message: CancelOrder) -> None:
        """Perform _handle_cancel."""
        current = self._manager.get_order(message.intent.order_id)
        if current.broker_order_id is None:
            raise RuntimeError("order must have broker_order_id before cancellation")
        order = self._manager.request_cancel(message.intent)
        assert order.broker_order_id is not None
        self._execution_ref.tell(
            OrderCancelRequest(
                order_id=order.order_id,
                broker_order_id=order.broker_order_id,
            )
        )

    def _handle_report(self, message: ExecutionReport) -> None:
        """Perform _handle_report."""
        self._fills.extend(self._execution_report_handler.handle(message))


__all__ = ["CancelOrder", "OrderManagerActor", "SubmitOrder"]
