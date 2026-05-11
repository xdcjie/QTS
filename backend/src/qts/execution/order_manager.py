"""Order manager MVP."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from qts.core.ids import InstrumentId, OrderId
from qts.domain.risk import RiskDecision
from qts.execution.idempotency import FillIdempotencyStore
from qts.execution.order_state_machine import OrderEvent, OrderState, OrderStateMachine


class OrderSide(StrEnum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """Approved order instruction before broker submission."""

    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")


@dataclass(frozen=True, slots=True)
class CancelIntent:
    """Intent to cancel an order through OrderManager."""

    order_id: OrderId
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReplaceIntent:
    """Intent to replace an order through OrderManager."""

    order_id: OrderId
    new_quantity: Decimal

    def __post_init__(self) -> None:
        if self.new_quantity <= Decimal("0"):
            raise ValueError("new_quantity must be positive")


@dataclass(frozen=True, slots=True)
class Order:
    """Order snapshot owned by OrderManager."""

    order_id: OrderId
    intent: OrderIntent
    state: OrderState
    broker_order_id: str | None = None


class ExecutionReportStatus(StrEnum):
    """Normalized broker report status."""

    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    """Normalized broker execution report."""

    report_id: str
    broker_order_id: str
    status: ExecutionReportStatus
    filled_quantity: Decimal = Decimal("0")
    fill_price: Decimal | None = None
    fill_id: str | None = None
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if self.filled_quantity < Decimal("0"):
            raise ValueError("filled_quantity must be non-negative")
        if self.commission < Decimal("0"):
            raise ValueError("commission must be non-negative")
        if self.slippage < Decimal("0"):
            raise ValueError("slippage must be non-negative")


@dataclass(frozen=True, slots=True)
class OrderFill:
    """OrderManager-validated fill event."""

    fill_id: str
    order_id: OrderId
    instrument_id: InstrumentId
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class OrderManagerResult:
    """Events emitted by processing an execution report."""

    order: Order
    fills: tuple[OrderFill, ...] = ()


@dataclass(frozen=True, slots=True)
class OrderManagerSnapshot:
    """Serializable OrderManager state for reconnect/recovery."""

    orders: tuple[Order, ...]
    broker_to_order: tuple[tuple[str, OrderId], ...]
    seen_fill_ids: tuple[str, ...] = ()


class OrderManager:
    """Owns order lifecycle and normalized execution reports."""

    def __init__(self) -> None:
        self._orders: dict[OrderId, Order] = {}
        self._machines: dict[OrderId, OrderStateMachine] = {}
        self._broker_to_order: dict[str, OrderId] = {}
        self._fill_ids = FillIdempotencyStore()
        self._fill_ids_by_order: dict[OrderId, set[str]] = {}

    def create_order(self, intent: OrderIntent, *, risk_decision: RiskDecision) -> Order:
        if not risk_decision.approved:
            raise ValueError("risk decision is not approved")
        machine = OrderStateMachine()
        order = Order(order_id=intent.order_id, intent=intent, state=machine.state)
        self._orders[order.order_id] = order
        self._machines[order.order_id] = machine
        return order

    def mark_sent(self, order_id: OrderId, *, broker_order_id: str) -> Order:
        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        machine = self._machines[order_id]
        state = machine.apply(OrderEvent.SENT)
        order = self._replace_order(order_id, state=state, broker_order_id=broker_order_id)
        self._broker_to_order[broker_order_id] = order_id
        return order

    def request_cancel(self, intent: CancelIntent) -> Order:
        state = self._machines[intent.order_id].apply(OrderEvent.CANCEL_REQUESTED)
        return self._replace_order(intent.order_id, state=state)

    def request_replace(self, intent: ReplaceIntent, *, risk_decision: RiskDecision) -> Order:
        if not risk_decision.approved:
            raise ValueError("risk decision is not approved")
        state = self._machines[intent.order_id].apply(OrderEvent.REPLACE_REQUESTED)
        current = self._orders[intent.order_id]
        replaced_intent = OrderIntent(
            order_id=current.intent.order_id,
            instrument_id=current.intent.instrument_id,
            side=current.intent.side,
            quantity=intent.new_quantity,
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
        order_id = self._broker_to_order[report.broker_order_id]
        state = self._machines[order_id].apply(self._event_for_report(report.status))
        order = self._replace_order(order_id, state=state)
        fills = self._fills_for_report(order, report)
        return OrderManagerResult(order=order, fills=fills)

    def get_order(self, order_id: OrderId) -> Order:
        return self._orders[order_id]

    def discard_order(self, order_id: OrderId) -> None:
        order = self._orders.pop(order_id)
        self._machines.pop(order_id, None)
        if order.broker_order_id is not None:
            self._broker_to_order.pop(order.broker_order_id, None)
        for fill_id in self._fill_ids_by_order.pop(order_id, set()):
            self._fill_ids.discard(fill_id)

    def snapshot(self) -> OrderManagerSnapshot:
        return OrderManagerSnapshot(
            orders=tuple(self._orders.values()),
            broker_to_order=tuple(self._broker_to_order.items()),
            seen_fill_ids=self._fill_ids.snapshot(),
        )

    @classmethod
    def restore(cls, snapshot: OrderManagerSnapshot) -> OrderManager:
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
            ),
        )

    @staticmethod
    def _event_for_report(status: ExecutionReportStatus) -> OrderEvent:
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
