from __future__ import annotations

import inspect
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from qts.core.ids import AccountId, CorrelationId, StrategyId
    from qts.runtime.actors.execution_actor import ExecutionAdapter
    from qts.runtime.actors.order_manager_actor import OrderRouteMetadata


def test_execution_actor_requires_explicit_execution_adapter() -> None:
    from qts.runtime.actors.execution_actor import ExecutionActor

    signature = inspect.signature(ExecutionActor)

    assert signature.parameters["execution_adapter"].default is inspect.Signature.empty


def test_execution_actor_uses_injected_simulated_adapter_and_emits_execution_report() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.execution.order_manager import ExecutionReport, OrderIntent, OrderSide
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import ExecutionActor, OrderExecutionRequest
    from qts.runtime.mailbox import Mailbox

    out = Mailbox()
    actor = ExecutionActor(
        order_manager_ref=ActorRef(mailbox=out),
        execution_adapter=_simulated_execution_adapter(),
    )
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
            account_id=AccountId("acct-a"),
            strategy_id=StrategyId("strategy-a"),
            route_metadata=_route_metadata(
                account_id=AccountId("acct-a"),
                strategy_id=StrategyId("strategy-a"),
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
            ),
        )
    )

    report = out.get()
    assert isinstance(report, ExecutionReport)
    assert report.broker_order_id == "sim-001"
    assert report.fill_price == Decimal("101.25")


def test_execution_actor_forwards_route_metadata_to_execution_adapter() -> None:
    from dataclasses import dataclass
    from typing import Any

    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.execution.order_manager import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderSide,
    )
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import ExecutionActor, OrderExecutionRequest
    from qts.runtime.mailbox import Mailbox

    @dataclass(slots=True)
    class RecordingAdapter:
        seen: dict[str, Any] | None = None

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
            bar_time: object | None = None,
        ) -> ExecutionReport:
            self.seen = {
                "intent": intent,
                "broker_order_id": broker_order_id,
                "market_price": market_price,
                "account_id": account_id,
                "strategy_id": strategy_id,
                "client_order_id": client_order_id,
                "correlation_id": correlation_id,
            }
            return ExecutionReport(
                report_id="rpt-001",
                broker_order_id=broker_order_id,
                status=ExecutionReportStatus.ACCEPTED,
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
            raise AssertionError("cancel should not be called")

    out = Mailbox()
    adapter = RecordingAdapter()
    actor = ExecutionActor(order_manager_ref=ActorRef(mailbox=out), execution_adapter=adapter)
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    actor.handle(
        OrderExecutionRequest(
            intent=intent,
            broker_order_id="broker-001",
            market_price=Decimal("101.25"),
            account_id=AccountId("acct-a"),
            strategy_id=StrategyId("strategy-a"),
            route_metadata=_route_metadata(
                account_id=AccountId("acct-a"),
                strategy_id=StrategyId("strategy-a"),
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
            ),
        )
    )

    assert adapter.seen == {
        "intent": intent,
        "broker_order_id": "broker-001",
        "market_price": Decimal("101.25"),
        "account_id": AccountId("acct-a"),
        "strategy_id": StrategyId("strategy-a"),
        "client_order_id": "client-001",
        "correlation_id": CorrelationId("corr-001"),
    }


def _route_metadata(
    *,
    account_id: AccountId,
    strategy_id: StrategyId,
    client_order_id: str,
    correlation_id: CorrelationId,
) -> OrderRouteMetadata:
    from qts.core.ids import BrokerId
    from qts.runtime.actors.order_manager_actor import OrderRouteMetadata

    return OrderRouteMetadata(
        broker_id=BrokerId("broker-route"),
        account_id=account_id,
        strategy_id=strategy_id,
        client_order_id=client_order_id,
        correlation_id=correlation_id,
    )


def _simulated_execution_adapter() -> ExecutionAdapter:
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.runtime.config import BacktestCostModel

    return SimulatedExecutionAdapter(cost_model=BacktestCostModel())


def test_execution_actor_rejects_market_data_messages() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Tick
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import ExecutionActor
    from qts.runtime.mailbox import Mailbox

    actor = ExecutionActor(
        order_manager_ref=ActorRef(mailbox=Mailbox()),
        execution_adapter=_simulated_execution_adapter(),
    )

    with pytest.raises(TypeError, match="unsupported execution message"):
        actor.handle(
            Tick(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
                price=Decimal("101.25"),
                size=Decimal("10"),
            )
        )
