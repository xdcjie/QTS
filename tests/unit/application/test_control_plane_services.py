"""Contract tests for the control-plane query/control application services.

These lock the documented behavior of StrategyControlService, OrderQueryService,
and AccountQueryService: each reads from a real domain source and derives an
honest value (not a literal) when no live source is bound.
"""

from __future__ import annotations

from decimal import Decimal

from qts.application.services import (
    AccountQueryService,
    OrderQueryService,
    StrategyControlService,
)
from qts.application.strategy_lifecycle import StrategyInstance
from qts.core.ids import AccountId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import Order, OrderIntent, OrderSide, OrderState, OrderStateSnapshot
from qts.runtime.actors.account_actor import AccountActor


def test_strategy_control_service_reflects_lifecycle_transitions() -> None:
    service = StrategyControlService.with_configured_strategies(
        (
            StrategyInstance(
                strategy_id=StrategyId("strategy-001"),
                class_path="examples.strategies.hello_world.HelloWorldStrategy",
                account_id=AccountId("acct-001"),
            ),
        )
    )

    listed = service.list_strategies()
    assert len(listed) == 1
    assert listed[0].strategy_id == "strategy-001"
    assert listed[0].status == "stopped"
    assert service.start("strategy-001").status == "running"
    assert service.list_strategies()[0].status == "running"
    assert service.stop("strategy-001").status == "stopped"


def test_order_query_service_reads_state_from_bound_source() -> None:
    intent = OrderIntent(
        order_id=OrderId("ord-1"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )
    snapshot = OrderStateSnapshot(
        orders=(Order(order_id=OrderId("ord-1"), intent=intent, state=OrderState.FILLED),),
        broker_to_order=(),
    )

    class _Source:
        def snapshot(self) -> OrderStateSnapshot:
            return snapshot

    service = OrderQueryService(_Source())

    assert service.order_status("ord-1").status == "filled"
    # Unknown order is derived as not_found from the queried snapshot.
    assert service.order_status("ord-missing").status == "not_found"


def test_order_query_service_derives_not_found_without_source() -> None:
    service = OrderQueryService()
    result = service.order_status("ord-1")
    assert result.status == "not_found"


def test_account_query_service_reads_cash_from_account_actor() -> None:
    actor = AccountActor(
        initial_cash={"USD": Decimal("1000.25")},
        account_id=AccountId("acct-1"),
    )
    service = AccountQueryService({"acct-1": actor})

    snapshot = service.account_snapshot("acct-1")

    assert snapshot.account_id == "acct-1"
    assert snapshot.cash == {"USD": "1000.25"}


def test_account_query_service_derives_empty_cash_without_source() -> None:
    service = AccountQueryService()
    snapshot = service.account_snapshot("acct-unbound")
    assert snapshot.cash == {}
