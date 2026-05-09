from __future__ import annotations

from decimal import Decimal

import pytest


def test_execution_actor_wraps_simulator_and_emits_execution_report() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import ExecutionReport, OrderIntent, OrderSide
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import ExecutionActor, OrderExecutionRequest
    from qts.runtime.mailbox import Mailbox

    out = Mailbox()
    actor = ExecutionActor(order_manager_ref=ActorRef(mailbox=out))
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    actor.handle(
        OrderExecutionRequest(
            intent=intent,
            broker_order_id="sim-001",
            market_price=Decimal("101.25"),
        )
    )

    report = out.get()
    assert isinstance(report, ExecutionReport)
    assert report.broker_order_id == "sim-001"
    assert report.fill_price == Decimal("101.25")


def test_execution_actor_rejects_market_data_messages() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Tick
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import ExecutionActor
    from qts.runtime.mailbox import Mailbox

    actor = ExecutionActor(order_manager_ref=ActorRef(mailbox=Mailbox()))

    with pytest.raises(TypeError, match="unsupported execution message"):
        actor.handle(
            Tick(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
                price=Decimal("101.25"),
                size=Decimal("10"),
            )
        )
