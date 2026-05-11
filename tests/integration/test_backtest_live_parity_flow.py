from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId, OrderId
from qts.domain.market_data import Bar
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
)
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import Strategy


@dataclass(slots=True)
class RecordingExecutionAdapter:
    seen: list[OrderIntent] = field(default_factory=list)

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        self.seen.append(intent)
        return ExecutionReport(
            report_id=f"{broker_order_id}-report",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill",
        )


def test_shared_actor_order_flow_uses_same_messages_for_execution_adapters() -> None:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    adapter = RecordingExecutionAdapter()
    account_actor = AccountActor(initial_cash={"USD": Decimal("1000")})
    account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
    execution_mailbox = Mailbox()
    order_manager_mailbox = Mailbox()
    order_manager_actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=account_ref,
        multiplier_by_instrument={instrument_id: Decimal("1")},
    )
    order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
    execution_ref = ActorRef(
        actor=ExecutionActor(order_manager_ref=order_manager_ref, execution_adapter=adapter),
        mailbox=execution_mailbox,
    )
    intent = OrderIntent(
        order_id=OrderId("order-1"),
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )

    order_manager_ref.tell(
        SubmitOrder(
            intent=intent,
            risk_decision=RiskDecision.approve(),
            broker_order_id="adapter-order-1",
            market_price=Decimal("100"),
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()

    assert adapter.seen == [intent]
    assert order_manager_actor.get_order(OrderId("order-1")).state.value == "filled"
    assert order_manager_actor.fills[0].instrument_id == instrument_id
    assert account_actor.snapshot().positions[instrument_id].quantity == Decimal("2")
    assert account_actor.snapshot().cash["USD"] == Decimal("800")


def test_backtest_risk_rejection_does_not_submit_order_or_mutate_account() -> None:
    class BuyOnce(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("1"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bar = Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        is_complete=True,
    )

    result = BacktestEngine(
        strategy=BuyOnce(),
        bars=[bar],
        initial_cash=Decimal("1000"),
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("50"))]),
    ).run()

    assert result.orders == ()
    assert result.fills == ()
    assert result.final_account.cash["USD"] == Decimal("1000")
    assert result.final_account.positions == {}
