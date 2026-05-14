from __future__ import annotations

from decimal import Decimal


def test_target_to_fill_updates_account_through_actor_messages() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.risk import OrderRiskRequest
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.execution.order_state_machine import OrderState
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.actors.execution_actor import ExecutionActor
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    account_id = AccountId("acct-shared-flow")
    strategy_id = StrategyId("strategy-shared-flow")
    account_actor = AccountActor(
        initial_cash={"USD": Decimal("10000")},
        account_id=account_id,
    )
    account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
    execution_mailbox = Mailbox()
    order_manager_mailbox = Mailbox()
    order_manager_actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=account_ref,
        account_id=account_id,
    )
    order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
    execution_actor = ExecutionActor(order_manager_ref=order_manager_ref)
    execution_ref = ActorRef(actor=execution_actor, mailbox=execution_mailbox)

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    risk = RiskEngine([MaxNotionalRule(max_notional=Decimal("5000"))])
    risk_decision = risk.check(
        OrderRiskRequest(
            instrument_id=instrument_id,
            quantity=Decimal("10"),
            price=Decimal("100"),
            multiplier=Decimal("1"),
        )
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    order_manager_ref.tell(
        SubmitOrder(
            intent=intent,
            risk_decision=risk_decision,
            broker_order_id="sim-001",
            market_price=Decimal("100"),
            account_id=account_id,
            strategy_id=strategy_id,
            client_order_id="client-001",
            correlation_id=CorrelationId("corr-001"),
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()

    snapshot = account_actor.snapshot()
    assert snapshot.positions[instrument_id].quantity == Decimal("10")
    assert snapshot.cash["USD"] == Decimal("9000")
    assert order_manager_actor.get_order(intent.order_id).state is OrderState.FILLED
