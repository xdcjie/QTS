"""Order execution actor MVP."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol

from qts.core.ids import AccountId, CorrelationId, OrderId, StrategyId
from qts.execution.order_manager import ExecutionReport, OrderIntent
from qts.execution.simulator.simulated_broker import SimulatedBroker
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef

if TYPE_CHECKING:
    from qts.runtime.actors.order_manager_actor import OrderRouteMetadata


class ExecutionAdapter(Protocol):
    """Execution boundary contract used by the actor."""

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Execute a market order."""
        ...

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Cancel an active order."""
        ...


@dataclass(frozen=True, slots=True)
class OrderExecutionRequest:
    """Message requesting order execution."""

    intent: OrderIntent
    broker_order_id: str
    market_price: Decimal
    account_id: AccountId
    strategy_id: StrategyId
    route_metadata: OrderRouteMetadata

    def __post_init__(self) -> None:
        """Validate execution request identity fields."""
        if self.route_metadata.account_id != self.account_id:
            raise ValueError("execution account_id does not match route metadata")
        if self.route_metadata.strategy_id != self.strategy_id:
            raise ValueError("execution strategy_id does not match route metadata")


@dataclass(frozen=True, slots=True)
class OrderCancelRequest:
    """Message requesting broker order cancellation."""

    order_id: OrderId
    broker_order_id: str
    account_id: AccountId
    strategy_id: StrategyId
    route_metadata: OrderRouteMetadata

    def __post_init__(self) -> None:
        """Validate cancel request identity fields."""
        if self.route_metadata.account_id != self.account_id:
            raise ValueError("cancel account_id does not match route metadata")
        if self.route_metadata.strategy_id != self.strategy_id:
            raise ValueError("cancel strategy_id does not match route metadata")


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
        """Perform handle."""
        if isinstance(message, OrderExecutionRequest):
            report = self._execution_adapter.execute_market_order(
                message.intent,
                broker_order_id=message.broker_order_id,
                market_price=message.market_price,
                account_id=message.account_id,
                strategy_id=message.strategy_id,
                client_order_id=message.route_metadata.client_order_id,
                correlation_id=message.route_metadata.correlation_id,
            )
            self._order_manager_ref.tell(report)
            return
        if isinstance(message, OrderCancelRequest):
            report = self._execution_adapter.cancel_order(
                message.order_id,
                broker_order_id=message.broker_order_id,
                account_id=message.account_id,
                strategy_id=message.strategy_id,
                client_order_id=message.route_metadata.client_order_id,
                correlation_id=message.route_metadata.correlation_id,
            )
            self._order_manager_ref.tell(report)
            return
        raise TypeError(f"unsupported execution message: {type(message).__name__}")


__all__ = ["ExecutionActor", "OrderCancelRequest", "OrderExecutionRequest"]
