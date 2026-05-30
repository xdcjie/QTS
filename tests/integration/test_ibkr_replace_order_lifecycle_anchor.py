"""Anchor: the IBKR replace lifecycle is honestly capability-gated.

QTS-FINAL-007 makes ReplaceOrder a complete capability gated by
``BrokerCapabilities.supports_replace``. The IBKR brokerage models do not yet
implement a TWS order-modify path, so they advertise ``supports_replace=False``;
a replace routed to an IBKR-configured runtime must therefore be rejected with
the typed ``UnsupportedOrderReplace`` domain error at the capability gate (not
silently swallowed, and not a pseudo-successful handled message).

This anchor locks two invariants so the IBKR replace path cannot regress into a
dishonest no-op, and so that the day the TWS modify lands the capability flag and
this anchor are updated together:

1. Every IBKR brokerage model advertises ``supports_replace=False``.
2. An OrderManagerActor wired with IBKR capabilities rejects a replace with
   ``UnsupportedOrderReplace`` and leaves the order unchanged.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import OrderIntent, OrderSide, ReplaceIntent
from qts.domain.risk import RiskDecision
from qts.execution.adapters.brokerage_capabilities import broker_capabilities_for_model
from qts.execution.errors import UnsupportedOrderReplace
from qts.execution.order_state_machine import OrderState
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.order_manager_actor import OrderManagerActor, ReplaceOrder, SubmitOrder
from qts.runtime.mailbox import Mailbox
from qts.runtime.order_route_metadata import OrderRouteMetadata

_IBKR_MODELS = ("IBKR_EQUITY", "IBKR_FUTURES", "IBKR_OPTIONS")
_ACCOUNT = AccountId("acct-ibkr")
_STRATEGY = StrategyId("strategy-ibkr")
_ORDER = OrderId("ord-ibkr-replace")


@pytest.mark.parametrize("model", _IBKR_MODELS)
def test_ibkr_models_do_not_advertise_replace_support(model: str) -> None:
    assert broker_capabilities_for_model(model).supports_replace is False


def test_ibkr_runtime_rejects_replace_with_unsupported_domain_error() -> None:
    capabilities = broker_capabilities_for_model("IBKR_EQUITY")
    execution = Mailbox()
    route = OrderRouteMetadata(
        broker_id=BrokerId("ibkr-equity"),
        account_id=_ACCOUNT,
        strategy_id=_STRATEGY,
        client_order_id="client-ibkr",
        correlation_id=CorrelationId("corr-ibkr"),
    )
    actor = OrderManagerActor(
        account_id=_ACCOUNT,
        execution_ref=ActorRef(mailbox=execution),
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
            broker_order_id="ibkr-broker-1",
            market_price=Decimal("101"),
            account_id=_ACCOUNT,
            strategy_id=_STRATEGY,
            route_metadata=route,
        )
    )
    assert execution.get() is not None  # drain the submit request

    with pytest.raises(UnsupportedOrderReplace, match="does not support order replacement"):
        actor.handle(
            ReplaceOrder(
                intent=ReplaceIntent(order_id=_ORDER, new_quantity=Decimal("20")),
                risk_decision=RiskDecision.approve(),
                account_id=_ACCOUNT,
                strategy_id=_STRATEGY,
                route_metadata=route,
            )
        )

    # No broker replace request is routed and the order is unchanged.
    assert execution.empty()
    order = actor.get_order(_ORDER)
    assert order.intent.quantity == Decimal("10")
    assert order.state is OrderState.SENT
