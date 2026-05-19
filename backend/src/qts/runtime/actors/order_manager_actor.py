"""OrderManager actor MVP."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
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
class OrderRouteMetadata:
    """Route and trace metadata captured when an order is submitted."""

    broker_id: BrokerId
    account_id: AccountId
    strategy_id: StrategyId
    client_order_id: str
    correlation_id: CorrelationId
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    aggregation_decision_id: str | None = None

    def __post_init__(self) -> None:
        """Validate route and trace metadata."""
        if not self.client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        if self.aggregation_decision_id is not None and not self.aggregation_decision_id.strip():
            raise ValueError("aggregation_decision_id must not be empty")

    def to_payload(self) -> dict[str, str]:
        """Serialize route metadata for recovery snapshots."""
        payload = {
            "broker_id": self.broker_id.value,
            "account_id": self.account_id.value,
            "strategy_id": self.strategy_id.value,
            "client_order_id": self.client_order_id,
            "correlation_id": self.correlation_id.value,
        }
        if self.contributing_strategy_ids:
            payload["contributing_strategy_ids"] = ",".join(
                strategy_id.value for strategy_id in self.contributing_strategy_ids
            )
        if self.aggregation_decision_id is not None:
            payload["aggregation_decision_id"] = self.aggregation_decision_id
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> OrderRouteMetadata:
        """Restore route metadata from a recovery snapshot payload."""
        raw_contributors = payload.get("contributing_strategy_ids", "")
        if isinstance(raw_contributors, str):
            contributing_strategy_ids = tuple(
                StrategyId(value) for value in raw_contributors.split(",") if value
            )
        elif isinstance(raw_contributors, Iterable):
            contributing_strategy_ids = tuple(StrategyId(str(value)) for value in raw_contributors)
        else:
            contributing_strategy_ids = ()
        return cls(
            broker_id=BrokerId(str(payload["broker_id"])),
            account_id=AccountId(str(payload["account_id"])),
            strategy_id=StrategyId(str(payload["strategy_id"])),
            client_order_id=str(payload["client_order_id"]),
            correlation_id=CorrelationId(str(payload["correlation_id"])),
            contributing_strategy_ids=contributing_strategy_ids,
            aggregation_decision_id=(
                str(payload["aggregation_decision_id"])
                if payload.get("aggregation_decision_id") is not None
                else None
            ),
        )

    def matches_route(self, route_metadata: OrderRouteMetadata) -> bool:
        """Return whether command route identity matches the submitted order route."""
        return self == route_metadata


class OrderManagerActor(Actor):
    """Actor-owned OrderManager wrapper."""

    def __init__(
        self,
        *,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        account_id: AccountId | None = None,
        multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None = None,
    ) -> None:
        """Perform __init__."""
        self._account_id = account_id
        self._manager = OrderManager()
        self._execution_ref = execution_ref
        self._execution_report_handler = ExecutionReportHandler(
            order_manager=self._manager,
            account_ref=account_ref,
            multiplier_by_instrument=multiplier_by_instrument,
            account_id=account_id,
        )
        self._fills: list[OrderFill] = []
        self._route_metadata_by_order_id: dict[OrderId, OrderRouteMetadata] = {}

    def handle(self, message: object) -> None:
        """Perform handle."""
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

    def snapshot(self) -> OrderStateSnapshot:
        """Return actor-owned order manager snapshot."""
        return self._manager.snapshot()

    def route_metadata(self, order_id: OrderId) -> OrderRouteMetadata:
        """Return route metadata captured for an active order."""
        return self._route_metadata_by_order_id[order_id]

    def compact_for_streaming(self, order_ids: Iterable[OrderId]) -> None:
        """Perform compact_for_streaming."""
        for order_id in order_ids:
            self._manager.discard_terminal_order(order_id)
        self._fills.clear()

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
        raise NotImplementedError("replace order execution is not implemented")

    def _handle_report(self, message: ExecutionReport) -> None:
        """Perform _handle_report."""
        self._fills.extend(self._execution_report_handler.handle(message))


__all__ = [
    "CancelOrder",
    "OrderManagerActor",
    "OrderRouteMetadata",
    "ReplaceOrder",
    "SubmitOrder",
]
