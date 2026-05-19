"""Order execution actor MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from qts.core.ids import AccountId, OrderId, StrategyId
from qts.domain.orders import OrderIntent
from qts.execution.execution_adapter import ExecutionAdapter
from qts.runtime.actor import Actor
from qts.runtime.actor_ref import ActorRef
from qts.runtime.live_capital import LiveCapitalOrderDecision

if TYPE_CHECKING:
    from qts.runtime.actors.order_manager_actor import OrderRouteMetadata


@dataclass(frozen=True, slots=True)
class OrderExecutionRequest:
    """Message requesting order execution."""

    intent: OrderIntent
    broker_order_id: str
    market_price: Decimal
    account_id: AccountId
    strategy_id: StrategyId
    route_metadata: OrderRouteMetadata
    bar_time: datetime | None = None

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
        execution_adapter: ExecutionAdapter,
        live_capital_decision: LiveCapitalOrderDecision | None = None,
    ) -> None:
        self._order_manager_ref = order_manager_ref
        self._execution_adapter = execution_adapter
        self._live_capital_decision = live_capital_decision

    def handle(self, message: object) -> None:
        """Perform handle."""
        if isinstance(message, OrderExecutionRequest):
            if self._live_capital_decision is not None:
                self._live_capital_decision.assert_live_order_allowed()
            report = self._execution_adapter.execute_market_order(
                message.intent,
                broker_order_id=message.broker_order_id,
                market_price=message.market_price,
                account_id=message.account_id,
                strategy_id=message.strategy_id,
                client_order_id=message.route_metadata.client_order_id,
                correlation_id=message.route_metadata.correlation_id,
                bar_time=message.bar_time,
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
