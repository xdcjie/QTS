"""Gate tests: ReplaceOrder produces a capability-gated structured rejection (DR-026)."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import OrderIntent, OrderSide, ReplaceIntent
from qts.domain.risk import RiskDecision
from qts.execution.broker import BrokerCapabilities
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.order_manager_actor import (
    OrderManagerActor,
    ReplaceOrder,
    SubmitOrder,
)
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


def _actor(capabilities: BrokerCapabilities | None) -> OrderManagerActor:
    actor = OrderManagerActor(
        account_id=_ACCOUNT,
        execution_ref=ActorRef(mailbox=Mailbox()),
        account_ref=ActorRef(mailbox=Mailbox()),
        capabilities=capabilities,
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
    return actor


def _replace(actor: OrderManagerActor) -> None:
    actor.handle(
        ReplaceOrder(
            intent=ReplaceIntent(order_id=_ORDER, new_quantity=Decimal("20")),
            risk_decision=RiskDecision.approve(),
            account_id=_ACCOUNT,
            strategy_id=_STRATEGY,
            route_metadata=_route(),
        )
    )


def test_replace_on_unsupported_broker_is_structured_rejection_without_raising() -> None:
    actor = _actor(capabilities=None)
    _replace(actor)  # must not raise
    rejection = actor.replace_rejections[-1]
    assert rejection.order_id == _ORDER
    assert rejection.reason_code == "REPLACE_NOT_SUPPORTED"
    # Order is left unchanged by a rejected replace.
    assert actor.get_order(_ORDER).intent.quantity == Decimal("10")


def test_replace_on_replace_capable_broker_defers_with_not_implemented() -> None:
    actor = _actor(
        capabilities=BrokerCapabilities(broker_id=BrokerId("simulated"), supports_replace=True)
    )
    _replace(actor)  # must not raise
    rejection = actor.replace_rejections[-1]
    assert rejection.reason_code == "REPLACE_NOT_IMPLEMENTED"
    assert actor.get_order(_ORDER).intent.quantity == Decimal("10")
