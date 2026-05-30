"""ReplaceOrder on a replace-capable broker routes to the execution actor.

QTS-FINAL-007: when ``BrokerCapabilities.supports_replace`` is true, the
OrderManagerActor transitions the order to ``REPLACE_REQUESTED`` (recording the
new quantity) and sends an ``OrderReplaceRequest`` to the execution actor. The
broker's ``ACCEPTED`` execution report then confirms the replace through the
normal report path (``REPLACE_REQUESTED -> ACCEPTED``).
"""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
    ReplaceIntent,
)
from qts.domain.risk import RiskDecision
from qts.execution.broker import BrokerCapabilities
from qts.execution.order_state_machine import OrderState
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.execution_actor import OrderExecutionRequest, OrderReplaceRequest
from qts.runtime.actors.order_manager_actor import OrderManagerActor, ReplaceOrder, SubmitOrder
from qts.runtime.mailbox import Mailbox
from qts.runtime.order_route_metadata import OrderRouteMetadata

_ACCOUNT = AccountId("acct-a")
_STRATEGY = StrategyId("strategy-a")
_ORDER = OrderId("ord-replace")


def _route() -> OrderRouteMetadata:
    return OrderRouteMetadata(
        broker_id=BrokerId("simulated"),
        account_id=_ACCOUNT,
        strategy_id=_STRATEGY,
        client_order_id="client-replace",
        correlation_id=CorrelationId("corr-replace"),
    )


def test_replace_capable_broker_routes_replace_request_then_confirms() -> None:
    execution = Mailbox()
    actor = OrderManagerActor(
        account_id=_ACCOUNT,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
        capabilities=BrokerCapabilities(broker_id=BrokerId("simulated"), supports_replace=True),
    )
    actor.handle(
        SubmitOrder(
            intent=OrderIntent(
                order_id=_ORDER,
                account_id=_ACCOUNT,
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("10"),
            ),
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-replace",
            market_price=Decimal("101"),
            account_id=_ACCOUNT,
            strategy_id=_STRATEGY,
            route_metadata=_route(),
        )
    )
    assert isinstance(execution.get(), OrderExecutionRequest)  # drain the submit request

    actor.handle(
        ReplaceOrder(
            intent=ReplaceIntent(order_id=_ORDER, new_quantity=Decimal("20")),
            risk_decision=RiskDecision.approve(),
            account_id=_ACCOUNT,
            strategy_id=_STRATEGY,
            route_metadata=_route(),
        )
    )

    replace_request = execution.get()
    assert isinstance(replace_request, OrderReplaceRequest)
    assert replace_request.order_id == _ORDER
    assert replace_request.broker_order_id == "broker-replace"
    assert replace_request.new_quantity == Decimal("20")
    assert replace_request.route_metadata.client_order_id == "client-replace"

    # OrderManager already reflects the requested replace.
    assert actor.get_order(_ORDER).state is OrderState.REPLACE_REQUESTED
    assert actor.get_order(_ORDER).intent.quantity == Decimal("20")

    # The broker's ACCEPTED ack confirms the replace.
    actor.handle(
        ExecutionReport(
            report_id="broker-replace-replace-1",
            broker_order_id="broker-replace",
            status=ExecutionReportStatus.ACCEPTED,
        )
    )
    assert actor.get_order(_ORDER).state is OrderState.ACCEPTED
