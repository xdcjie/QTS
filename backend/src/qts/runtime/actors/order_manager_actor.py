"""OrderManager actor MVP."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast

from qts.core.ids import AccountId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import (
    CancelIntent,
    ExecutionReport,
    Order,
    OrderFill,
    OrderIntent,
    OrderStateSnapshot,
    ReplaceIntent,
)
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import OrderManager
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorUnhandledMessageError
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import ApplyFill
from qts.runtime.actors.execution_actor import OrderCancelRequest, OrderExecutionRequest
from qts.runtime.execution_report_handler import ExecutionReportHandler
from qts.runtime.order_route_metadata import OrderRouteMetadata


@dataclass(frozen=True, slots=True)
class GetOrderManagerSnapshot:
    """Ask the OrderManagerActor for its current order state snapshot."""

    def validate_response(self, response: object) -> OrderStateSnapshot:
        """Return a typed order manager snapshot."""
        if not isinstance(response, OrderStateSnapshot):
            raise TypeError("expected OrderStateSnapshot response")
        return response


@dataclass(frozen=True, slots=True)
class GetFillCount:
    """Ask the OrderManagerActor for its current fill count."""

    def validate_response(self, response: object) -> int:
        """Return a typed fill count."""
        if not isinstance(response, int):
            raise TypeError("expected int response")
        return response


@dataclass(frozen=True, slots=True)
class GetFillsSince:
    """Ask the OrderManagerActor for fills recorded from a given index."""

    index: int

    def validate_response(self, response: object) -> tuple[OrderFill, ...]:
        """Return typed fills."""
        if not isinstance(response, tuple) or not all(
            isinstance(fill, OrderFill) for fill in response
        ):
            raise TypeError("expected OrderFill tuple response")
        return cast(tuple[OrderFill, ...], response)


@dataclass(frozen=True, slots=True)
class GetOrder:
    """Ask the OrderManagerActor for a specific order by ID."""

    order_id: OrderId

    def validate_response(self, response: object) -> Order:
        """Return a typed order."""
        if not isinstance(response, Order):
            raise TypeError("expected Order response")
        return response


@dataclass(frozen=True, slots=True)
class GetRouteMetadata:
    """Ask the OrderManagerActor for the route metadata of a specific order."""

    order_id: OrderId

    def validate_response(self, response: object) -> OrderRouteMetadata:
        """Return typed route metadata."""
        if not isinstance(response, OrderRouteMetadata):
            raise TypeError("expected OrderRouteMetadata response")
        return response


@dataclass(frozen=True, slots=True)
class SubmitOrder:
    """Message to submit an approved order to an execution actor."""

    intent: OrderIntent
    risk_decision: RiskDecision
    broker_order_id: str
    market_price: Decimal
    account_id: AccountId
    strategy_id: StrategyId
    route_metadata: OrderRouteMetadata
    bar_time: datetime | None = None

    def __post_init__(self) -> None:
        """Validate order submission identity fields."""
        if self.route_metadata.account_id != self.account_id:
            raise ValueError("SubmitOrder account_id does not match route metadata")
        if self.route_metadata.strategy_id != self.strategy_id:
            raise ValueError("SubmitOrder strategy_id does not match route metadata")


@dataclass(frozen=True, slots=True)
class CancelOrder:
    """Message to cancel an active order through the execution actor."""

    intent: CancelIntent
    account_id: AccountId
    strategy_id: StrategyId
    route_metadata: OrderRouteMetadata

    def __post_init__(self) -> None:
        """Validate order cancellation identity fields."""
        if self.route_metadata.account_id != self.account_id:
            raise ValueError("CancelOrder account_id does not match route metadata")
        if self.route_metadata.strategy_id != self.strategy_id:
            raise ValueError("CancelOrder strategy_id does not match route metadata")


@dataclass(frozen=True, slots=True)
class ReplaceOrder:
    """Message to replace an active order through the execution actor."""

    intent: ReplaceIntent
    risk_decision: RiskDecision
    account_id: AccountId
    strategy_id: StrategyId
    route_metadata: OrderRouteMetadata

    def __post_init__(self) -> None:
        """Validate order replacement identity fields."""
        if self.route_metadata.account_id != self.account_id:
            raise ValueError("ReplaceOrder account_id does not match route metadata")
        if self.route_metadata.strategy_id != self.strategy_id:
            raise ValueError("ReplaceOrder strategy_id does not match route metadata")


@dataclass(frozen=True, slots=True)
class CompactForStreaming:
    """Command to compact terminal orders and clear fill history."""

    order_ids: tuple[OrderId, ...]


class OrderManagerActor(Actor):
    """Actor-owned OrderManager wrapper."""

    def __init__(
        self,
        *,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        account_id: AccountId | None = None,
        multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None = None,
        currency: str = "USD",
    ) -> None:
        """Perform __init__."""
        self._account_id = account_id
        self._manager = OrderManager()
        self._execution_ref = execution_ref
        self._account_ref = account_ref
        self._multiplier_by_instrument = dict(multiplier_by_instrument or {})
        self._currency = currency
        self._execution_report_handler = ExecutionReportHandler(
            order_manager=self._manager,
            account_id=account_id,
        )
        self._fills_list: list[OrderFill] = []
        self._route_metadata_by_order_id: dict[OrderId, OrderRouteMetadata] = {}

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, tuple) and len(message) == 2:
            query, response_mailbox = message
            if isinstance(query, GetOrderManagerSnapshot):
                response_mailbox.put(self.snapshot())
                return
            if isinstance(query, GetFillCount):
                response_mailbox.put(self.fill_count)
                return
            if isinstance(query, GetFillsSince):
                response_mailbox.put(self.fills_since(query.index))
                return
            if isinstance(query, GetOrder):
                response_mailbox.put(self.get_order(query.order_id))
                return
            if isinstance(query, GetRouteMetadata):
                response_mailbox.put(self.route_metadata(query.order_id))
                return
        if isinstance(message, SubmitOrder):
            self._handle_submit(message)
            return
        if isinstance(message, CancelOrder):
            self._handle_cancel(message)
            return
        if isinstance(message, ReplaceOrder):
            self._handle_replace(message)
            return
        if isinstance(message, ExecutionReport):
            self._handle_report(message)
            return
        if isinstance(message, CompactForStreaming):
            self._compact_for_streaming(message.order_ids)
            return
        raise ActorUnhandledMessageError(
            f"unsupported order manager message: {type(message).__name__}"
        )

    def get_order(self, order_id: OrderId) -> Order:
        """Return order by ID."""
        return self._manager.get_order(order_id)

    @property
    def fills(self) -> tuple[OrderFill, ...]:
        """Return all recorded fills."""
        return tuple(self._fills_list)

    @property
    def fill_count(self) -> int:
        """Return count of recorded fills."""
        return len(self._fills_list)

    def fills_since(self, index: int) -> tuple[OrderFill, ...]:
        """Return fills recorded after given index."""
        return tuple(self._fills_list[index:])

    def snapshot(self) -> OrderStateSnapshot:
        """Return actor-owned order manager snapshot."""
        return self._manager.snapshot()

    def route_metadata(self, order_id: OrderId) -> OrderRouteMetadata:
        """Return route metadata captured for an active order."""
        return self._route_metadata_by_order_id[order_id]

    def _compact_for_streaming(self, order_ids: Iterable[OrderId]) -> None:
        """Perform _compact_for_streaming."""
        for order_id in order_ids:
            self._manager.discard_terminal_order(order_id)
        self._fills_list.clear()

    def _handle_submit(self, message: SubmitOrder) -> None:
        """Perform _handle_submit."""
        if message.intent.account_id != message.account_id:
            raise ValueError("order account_id does not match SubmitOrder account_id")
        if self._account_id is not None and message.intent.account_id != self._account_id:
            raise ValueError("order account_id does not match OrderManagerActor account_id")
        order = self._manager.create_order(message.intent, risk_decision=message.risk_decision)
        self._route_metadata_by_order_id[message.intent.order_id] = message.route_metadata
        self._manager.mark_sent(order.order_id, broker_order_id=message.broker_order_id)
        self._execution_ref.tell(
            OrderExecutionRequest(
                intent=message.intent,
                broker_order_id=message.broker_order_id,
                market_price=message.market_price,
                account_id=message.account_id,
                strategy_id=message.strategy_id,
                route_metadata=message.route_metadata,
                bar_time=message.bar_time,
            )
        )

    def _handle_cancel(self, message: CancelOrder) -> None:
        """Perform _handle_cancel."""
        current = self._manager.get_order(message.intent.order_id)
        metadata = self._route_metadata_by_order_id[message.intent.order_id]
        if current.intent.account_id != message.account_id:
            raise ValueError("cancel account_id does not match order account_id")
        if not metadata.matches_route(message.route_metadata):
            raise ValueError("cancel route metadata does not match submitted order")
        if self._account_id is not None and message.account_id != self._account_id:
            raise ValueError("cancel account_id does not match OrderManagerActor account_id")
        if current.broker_order_id is None:
            raise RuntimeError("order must have broker_order_id before cancellation")
        order = self._manager.request_cancel(message.intent)
        assert order.broker_order_id is not None
        self._execution_ref.tell(
            OrderCancelRequest(
                order_id=order.order_id,
                broker_order_id=order.broker_order_id,
                account_id=message.account_id,
                strategy_id=message.strategy_id,
                route_metadata=message.route_metadata,
            )
        )

    def _handle_replace(self, message: ReplaceOrder) -> None:
        """Apply replacement state when the execution boundary supports it."""
        current = self._manager.get_order(message.intent.order_id)
        metadata = self._route_metadata_by_order_id[message.intent.order_id]
        if current.intent.account_id != message.account_id:
            raise ValueError("replace account_id does not match order account_id")
        if not metadata.matches_route(message.route_metadata):
            raise ValueError("replace route metadata does not match submitted order")
        if self._account_id is not None and message.account_id != self._account_id:
            raise ValueError("replace account_id does not match OrderManagerActor account_id")
        raise RuntimeError("replace order is not supported: broker supports_replace is False")

    def _handle_report(self, message: ExecutionReport) -> None:
        """Process execution report and route fills to the account actor."""
        fills = self._execution_report_handler.handle(message)
        for fill in fills:
            self._account_ref.tell(
                ApplyFill(
                    fill=fill,
                    currency=self._currency,
                    multiplier=self._multiplier_by_instrument.get(fill.instrument_id, Decimal("1")),
                    fill_time=message.fill_time,
                )
            )
        self._fills_list.extend(fills)


__all__ = [
    "CancelOrder",
    "CompactForStreaming",
    "GetFillCount",
    "GetFillsSince",
    "GetOrder",
    "GetOrderManagerSnapshot",
    "GetRouteMetadata",
    "OrderManagerActor",
    "ReplaceOrder",
    "SubmitOrder",
]
