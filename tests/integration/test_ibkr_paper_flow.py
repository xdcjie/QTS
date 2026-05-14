from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qts.core.ids import AccountId, CorrelationId, OrderId, StrategyId
    from qts.domain.market_data import Tick
    from qts.execution.adapters.ibkr_order_execution import IbkrOrderRequest
    from qts.execution.order_manager import ExecutionReport, OrderIntent


def test_ibkr_paper_market_data_and_order_execution_use_separate_fake_transports() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.domain.risk import OrderRiskRequest
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.execution.order_state_machine import OrderState
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.actors.execution_actor import ExecutionActor
    from qts.runtime.actors.market_data_actor import MarketDataActor
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")

    market_data_adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=7497,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    order_adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=7497,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )

    market_data_subscriber = Mailbox()
    market_data_actor = MarketDataActor(subscribers=(ActorRef(mailbox=market_data_subscriber),))
    fake_market_data = _FakeIbkrMarketDataTransport(
        adapter=market_data_adapter,
        market_data_ref=ActorRef(actor=market_data_actor, mailbox=Mailbox()),
    )

    tick = fake_market_data.emit_tick(
        broker_symbol="AAPL",
        time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        price=Decimal("101.25"),
        size=Decimal("10"),
    )
    assert market_data_subscriber.get() == tick

    account_id = AccountId("acct-ibkr-paper")
    strategy_id = StrategyId("strategy-ibkr-paper")
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
    fake_execution = _FakeIbkrOrderExecutionTransport(adapter=order_adapter)
    execution_ref = ActorRef(
        actor=ExecutionActor(
            order_manager_ref=order_manager_ref,
            execution_adapter=fake_execution,
        ),
        mailbox=execution_mailbox,
    )

    risk_decision = RiskEngine([MaxNotionalRule(max_notional=Decimal("5000"))]).check(
        OrderRiskRequest(
            instrument_id=instrument_id,
            quantity=Decimal("10"),
            price=tick.price,
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
            broker_order_id="ibkr-001",
            market_price=tick.price,
            account_id=account_id,
            strategy_id=strategy_id,
            client_order_id="client-ibkr-001",
            correlation_id=CorrelationId("corr-ibkr-001"),
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()

    [request] = fake_execution.requests
    assert request.account_id == "DU1234567"
    assert request.broker_symbol == "AAPL"
    assert account_actor.snapshot().positions[instrument_id].quantity == Decimal("10")
    assert order_manager_actor.get_order(intent.order_id).state is OrderState.FILLED


@dataclass(slots=True)
class _FakeIbkrMarketDataTransport:
    adapter: object
    market_data_ref: object

    def emit_tick(
        self,
        *,
        broker_symbol: str,
        time: datetime,
        price: Decimal,
        size: Decimal,
    ) -> Tick:
        from qts.data.adapters.ibkr_market_data import IbkrMarketDataAdapter
        from qts.runtime.actor_ref import ActorRef
        from qts.runtime.actors.market_data_actor import MarketDataEvent

        assert isinstance(self.adapter, IbkrMarketDataAdapter)
        assert isinstance(self.market_data_ref, ActorRef)
        tick = self.adapter.normalize_tick(
            broker_symbol=broker_symbol,
            time=time,
            price=price,
            size=size,
        )
        self.market_data_ref.tell(MarketDataEvent(payload=tick))
        self.market_data_ref.process_all()
        return tick


@dataclass(slots=True)
class _FakeIbkrOrderExecutionTransport:
    adapter: object
    requests: list[IbkrOrderRequest] = field(default_factory=list)

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
        from qts.execution.adapters.ibkr_order_execution import (
            IbkrExecutionReport,
            IbkrOrderExecutionAdapter,
        )
        from qts.execution.broker import BrokerExecutionReportStatus

        assert isinstance(self.adapter, IbkrOrderExecutionAdapter)
        _ = account_id, strategy_id, correlation_id
        request = self.adapter.to_order_request(intent, client_order_id=client_order_id)
        self.requests.append(request)
        return self.adapter.normalize_execution_report(
            IbkrExecutionReport(
                report_id=f"rpt-{broker_order_id}",
                broker_order_id=broker_order_id,
                status=BrokerExecutionReportStatus.FILLED,
                filled_quantity=intent.quantity,
                fill_price=market_price,
                fill_id=f"fill-{broker_order_id}",
            )
        )

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
        from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus

        _ = order_id, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"rpt-cancel-{broker_order_id}",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )
