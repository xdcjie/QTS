"""Order manager MVP."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import OrderId
from qts.domain.orders import (
    CancelIntent,
    ExecutionReport,
    ExecutionReportStatus,
    Order,
    OrderFill,
    OrderIntent,
    OrderManagerResult,
    OrderManagerSnapshot,
    OrderSide,
    OrderState,
    ReplaceIntent,
)
from qts.domain.risk import RiskDecision
from qts.execution.idempotency import FillIdempotencyStore
from qts.execution.order_state_machine import OrderEvent, OrderStateMachine

_TERMINAL_ORDER_STATES = frozenset({OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED})


class OrderManager:
    """Owns order lifecycle and normalized execution reports."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._orders: dict[OrderId, Order] = {}
        self._machines: dict[OrderId, OrderStateMachine] = {}
        self._broker_to_order: dict[str, OrderId] = {}
        self._fill_ids = FillIdempotencyStore()
        self._fill_ids_by_order: dict[OrderId, set[str]] = {}

    def create_order(self, intent: OrderIntent, *, risk_decision: RiskDecision) -> Order:
        """Perform create_order."""
        if not risk_decision.approved:
            raise ValueError("risk decision is not approved")
        machine = OrderStateMachine()
        order = Order(order_id=intent.order_id, intent=intent, state=machine.state)
        self._orders[order.order_id] = order
        self._machines[order.order_id] = machine
        return order

    def mark_sent(self, order_id: OrderId, *, broker_order_id: str) -> Order:
        """Perform mark_sent."""
        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        machine = self._machines[order_id]
        state = machine.apply(OrderEvent.SENT)
        order = self._replace_order(order_id, state=state, broker_order_id=broker_order_id)
        self._broker_to_order[broker_order_id] = order_id
        return order

    def request_cancel(self, intent: CancelIntent) -> Order:
        """Perform request_cancel."""
        state = self._machines[intent.order_id].apply(OrderEvent.CANCEL_REQUESTED)
        return self._replace_order(intent.order_id, state=state)

    def request_replace(self, intent: ReplaceIntent, *, risk_decision: RiskDecision) -> Order:
        """Perform request_replace."""
        if not risk_decision.approved:
            raise ValueError("risk decision is not approved")
        state = self._machines[intent.order_id].apply(OrderEvent.REPLACE_REQUESTED)
        current = self._orders[intent.order_id]
        replaced_intent = OrderIntent(
            order_id=current.intent.order_id,
            instrument_id=current.intent.instrument_id,
            side=current.intent.side,
            quantity=intent.new_quantity,
            account_id=current.intent.account_id,
        )
        order = Order(
            order_id=current.order_id,
            intent=replaced_intent,
            state=state,
            broker_order_id=current.broker_order_id,
        )
        self._orders[intent.order_id] = order
        return order

    def process_report(self, report: ExecutionReport) -> OrderManagerResult:
        """Perform process_report."""
        order_id = self._broker_to_order[report.broker_order_id]
        state = self._machines[order_id].apply(self._event_for_report(report.status))
        order = self._replace_order(order_id, state=state)
        fills = self._fills_for_report(order, report)
        return OrderManagerResult(order=order, fills=fills)

    def get_order(self, order_id: OrderId) -> Order:
        """Perform get_order."""
        return self._orders[order_id]

    def discard_terminal_order(self, order_id: OrderId) -> None:
        """Perform discard_terminal_order."""
        order = self._orders[order_id]
        if order.state not in _TERMINAL_ORDER_STATES:
            raise ValueError(f"only terminal orders can be discarded: {order.state}")
        self._orders.pop(order_id)
        self._machines.pop(order_id, None)
        if order.broker_order_id is not None:
            self._broker_to_order.pop(order.broker_order_id, None)
        for fill_id in self._fill_ids_by_order.pop(order_id, set()):
            self._fill_ids.discard(fill_id)

    def snapshot(self) -> OrderManagerSnapshot:
        """Perform snapshot."""
        return OrderManagerSnapshot(
            orders=tuple(self._orders.values()),
            broker_to_order=tuple(self._broker_to_order.items()),
            seen_fill_ids=self._fill_ids.snapshot(),
        )

    @classmethod
    def restore(cls, snapshot: OrderManagerSnapshot) -> OrderManager:
        """Perform restore."""
        manager = cls()
        manager._orders = {order.order_id: order for order in snapshot.orders}
        manager._machines = {
            order.order_id: OrderStateMachine(state=order.state) for order in snapshot.orders
        }
        manager._broker_to_order = dict(snapshot.broker_to_order)
        manager._fill_ids = FillIdempotencyStore.restore(snapshot.seen_fill_ids)
        manager._fill_ids_by_order = {}
        return manager

    def _replace_order(
        self,
        order_id: OrderId,
        *,
        state: OrderState,
        broker_order_id: str | None = None,
    ) -> Order:
        """Perform _replace_order."""
        current = self._orders[order_id]
        order = Order(
            order_id=current.order_id,
            intent=current.intent,
            state=state,
            broker_order_id=(
                broker_order_id if broker_order_id is not None else current.broker_order_id
            ),
        )
        self._orders[order_id] = order
        return order

    def _fills_for_report(self, order: Order, report: ExecutionReport) -> tuple[OrderFill, ...]:
        """Perform _fills_for_report."""
        if report.filled_quantity <= Decimal("0") or report.fill_id is None:
            return ()
        if report.fill_price is None:
            raise ValueError("fill_price is required when filled_quantity is positive")
        if not self._fill_ids.mark_seen(report.fill_id):
            return ()
        self._fill_ids_by_order.setdefault(order.order_id, set()).add(report.fill_id)
        return (
            OrderFill(
                fill_id=report.fill_id,
                order_id=order.order_id,
                instrument_id=order.intent.instrument_id,
                side=order.intent.side,
                quantity=report.filled_quantity,
                price=report.fill_price,
                commission=report.commission,
                slippage=report.slippage,
                account_id=order.intent.account_id,
            ),
        )

    @staticmethod
    def _event_for_report(status: ExecutionReportStatus) -> OrderEvent:
        """Perform _event_for_report."""
        return {
            ExecutionReportStatus.ACCEPTED: OrderEvent.ACCEPTED,
            ExecutionReportStatus.PARTIALLY_FILLED: OrderEvent.PARTIALLY_FILLED,
            ExecutionReportStatus.FILLED: OrderEvent.FILLED,
            ExecutionReportStatus.CANCELLED: OrderEvent.CANCELLED,
            ExecutionReportStatus.REJECTED: OrderEvent.REJECTED,
        }[status]


__all__ = [
    "CancelIntent",
    "ExecutionReport",
    "ExecutionReportStatus",
    "Order",
    "OrderFill",
    "OrderIntent",
    "OrderManager",
    "OrderManagerResult",
    "OrderManagerSnapshot",
    "OrderSide",
    "ReplaceIntent",
]
