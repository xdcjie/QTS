from __future__ import annotations

from decimal import Decimal

from tests.support.order_route import order_route_metadata


def test_live_broker_callbacks_reuse_shared_order_and_account_flow() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.risk import RiskDecision
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.execution.order_state_machine import OrderState
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.actors.execution_actor import ExecutionActor
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox
    from qts.testing.fakes.broker import FakeBrokerAdapter

    broker = FakeBrokerAdapter(broker_id=BrokerId("paper"))
    execution_adapter = BrokerExecutionAdapter(
        broker=broker,
        account_id=AccountId("acct-a"),
    )
    account_id = AccountId("acct-a")
    strategy_id = StrategyId("strategy-a")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    account_actor = AccountActor(initial_cash={"USD": Decimal("1000")}, account_id=account_id)
    account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
    execution_mailbox = Mailbox()
    order_manager_mailbox = Mailbox()
    order_manager_actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=account_ref,
        multiplier_by_instrument={instrument_id: Decimal("1")},
        account_id=account_id,
    )
    order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
    execution_ref = ActorRef(
        actor=ExecutionActor(
            order_manager_ref=order_manager_ref,
            execution_adapter=execution_adapter,
        ),
        mailbox=execution_mailbox,
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )

    order_manager_ref.tell(
        SubmitOrder(
            intent=intent,
            risk_decision=RiskDecision.approve(),
            broker_order_id="runtime-broker-001",
            market_price=Decimal("100"),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=order_route_metadata(
                account_id=account_id,
                strategy_id=strategy_id,
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
            ),
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()

    assert order_manager_actor.get_order(intent.order_id).state is OrderState.ACCEPTED
    assert account_actor.snapshot().positions == {}

    broker_callback = broker.emit_fill(
        order_id=intent.order_id,
        quantity=Decimal("2"),
        price=Decimal("101"),
        fill_id="fill-001",
    )
    order_manager_ref.tell(execution_adapter.normalize_execution_report(broker_callback))
    order_manager_ref.process_all()
    account_ref.process_all()

    assert order_manager_actor.get_order(intent.order_id).state is OrderState.FILLED
    assert account_actor.snapshot().positions[instrument_id].quantity == Decimal("2")
    assert account_actor.snapshot().cash["USD"] == Decimal("798")


def test_live_cancel_flow_uses_order_manager_and_execution_actor_path() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import CancelIntent
    from qts.domain.risk import RiskDecision
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.execution.order_state_machine import OrderState
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.actors.execution_actor import ExecutionActor
    from qts.runtime.actors.order_manager_actor import CancelOrder, OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox
    from qts.testing.fakes.broker import FakeBrokerAdapter

    broker = FakeBrokerAdapter(broker_id=BrokerId("paper"))
    execution_adapter = BrokerExecutionAdapter(
        broker=broker,
        account_id=AccountId("acct-a"),
    )
    account_id = AccountId("acct-a")
    strategy_id = StrategyId("strategy-a")
    correlation_id = CorrelationId("corr-001")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    account_actor = AccountActor(initial_cash={"USD": Decimal("1000")}, account_id=account_id)
    account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
    execution_mailbox = Mailbox()
    order_manager_mailbox = Mailbox()
    order_manager_actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=account_ref,
        multiplier_by_instrument={instrument_id: Decimal("1")},
        account_id=account_id,
    )
    order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
    execution_ref = ActorRef(
        actor=ExecutionActor(
            order_manager_ref=order_manager_ref,
            execution_adapter=execution_adapter,
        ),
        mailbox=execution_mailbox,
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )

    order_manager_ref.tell(
        SubmitOrder(
            intent=intent,
            risk_decision=RiskDecision.approve(),
            broker_order_id="runtime-broker-001",
            market_price=Decimal("100"),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=order_route_metadata(
                account_id=account_id,
                strategy_id=strategy_id,
                client_order_id="client-001",
                correlation_id=correlation_id,
            ),
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    order_manager_ref.tell(
        CancelOrder(
            CancelIntent(order_id=intent.order_id),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=order_route_metadata(
                account_id=account_id,
                strategy_id=strategy_id,
                client_order_id="client-001",
                correlation_id=correlation_id,
            ),
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()

    assert order_manager_actor.get_order(intent.order_id).state is OrderState.CANCELLED
    assert account_actor.snapshot().positions == {}


def test_live_ibkr_fill_waits_for_commission_before_account_mutation() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.risk import RiskDecision
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import ExecutionReport, OrderIntent, OrderSide
    from qts.execution.order_state_machine import OrderState
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrExecutionPayload,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    ibkr_adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )
    account_id = AccountId("acct-ibkr-paper")
    strategy_id = StrategyId("strategy-ibkr-paper")
    account_actor = AccountActor(initial_cash={"USD": Decimal("1000")}, account_id=account_id)
    account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
    execution_mailbox = Mailbox()
    order_manager_actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=account_ref,
        multiplier_by_instrument={instrument_id: Decimal("1")},
        account_id=account_id,
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )
    order_manager_actor.handle(
        SubmitOrder(
            intent=intent,
            risk_decision=RiskDecision.approve(),
            broker_order_id="runtime-broker-001",
            market_price=Decimal("100"),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=order_route_metadata(
                account_id=account_id,
                strategy_id=strategy_id,
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
            ),
        )
    )

    pending = ibkr_adapter.on_execution(
        IbkrExecutionPayload(
            report_id="exec-001",
            broker_order_id="runtime-broker-001",
            execution_id="fill-001",
            filled_quantity=Decimal("2"),
            fill_price=Decimal("101"),
        )
    )
    assert pending is None
    assert account_actor.snapshot().positions == {}

    completed = ibkr_adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="fill-001",
            commission=Decimal("1.25"),
            currency="USD",
        )
    )
    assert isinstance(completed, ExecutionReport)
    order_manager_actor.handle(completed)
    account_ref.process_all()

    assert order_manager_actor.get_order(intent.order_id).state is OrderState.FILLED
    assert account_actor.snapshot().positions[instrument_id].quantity == Decimal("2")
    assert account_actor.snapshot().cash["USD"] == Decimal("796.75")
