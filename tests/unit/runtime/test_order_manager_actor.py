from __future__ import annotations

from decimal import Decimal

import pytest


def test_order_manager_actor_sends_broker_request_and_emits_validated_fill() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderSide,
    )
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import ApplyFill
    from qts.runtime.actors.execution_actor import OrderExecutionRequest
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    execution = Mailbox()
    account = Mailbox()
    actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution), account_ref=ActorRef(mailbox=account)
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    actor.handle(
        SubmitOrder(
            intent=intent,
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-001",
            market_price=Decimal("101"),
        )
    )
    execution_request = execution.get()
    assert isinstance(execution_request, OrderExecutionRequest)
    assert execution_request.intent == intent

    actor.handle(
        ExecutionReport(
            report_id="rpt-001",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.FILLED,
            filled_quantity=Decimal("10"),
            fill_price=Decimal("101"),
            fill_id="fill-001",
        )
    )

    fill_message = account.get()
    assert isinstance(fill_message, ApplyFill)
    assert fill_message.fill.quantity == Decimal("10")
    assert actor.get_order(intent.order_id).broker_order_id == "broker-001"


def test_order_manager_actor_does_not_send_risk_rejected_order_to_execution() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    execution = Mailbox()
    actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-rejected"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    with pytest.raises(ValueError, match="risk decision is not approved"):
        actor.handle(
            SubmitOrder(
                intent=intent,
                risk_decision=RiskDecision.rejected("BLOCKED", "blocked by test"),
                broker_order_id="broker-001",
                market_price=Decimal("101"),
            )
        )

    assert execution.empty()
