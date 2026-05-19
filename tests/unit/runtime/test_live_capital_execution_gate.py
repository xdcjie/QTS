from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

import pytest
from qts.runtime.live_capital import LiveCapitalOrderDecision


def test_live_order_blocked_without_live_order_permission() -> None:
    decision = _live_capital_decision(order_submission_permission="observation_only")

    with pytest.raises(PermissionError, match="LIVE_ORDER_PERMISSION_REQUIRED"):
        decision.assert_live_order_allowed()


def test_live_order_blocked_without_operator_signoff() -> None:
    decision = _live_capital_decision(operator_signoff_valid=False)

    with pytest.raises(PermissionError, match="LIVE_OPERATOR_SIGNOFF_REQUIRED"):
        decision.assert_live_order_allowed()


def test_live_order_blocked_when_reconciliation_not_clean() -> None:
    decision = _live_capital_decision(reconciliation_status="drift")

    with pytest.raises(PermissionError, match="LIVE_RECONCILIATION_NOT_CLEAN"):
        decision.assert_live_order_allowed()


def test_live_order_blocked_when_market_data_delayed() -> None:
    decision = _live_capital_decision(market_data_permission="delayed")

    with pytest.raises(PermissionError, match="LIVE_MARKET_DATA_PERMISSION_REQUIRED"):
        decision.assert_live_order_allowed()


def test_live_order_blocked_when_market_data_stale() -> None:
    decision = _live_capital_decision(market_data_freshness="stale")

    with pytest.raises(PermissionError, match="LIVE_MARKET_DATA_NOT_FRESH"):
        decision.assert_live_order_allowed()


def test_live_order_blocked_when_kill_switch_active() -> None:
    decision = _live_capital_decision(kill_switch_active=True)

    with pytest.raises(PermissionError, match="LIVE_KILL_SWITCH_ACTIVE"):
        decision.assert_live_order_allowed()


def test_execution_actor_enforces_live_order_gate_closest_to_adapter() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import OrderIntent, OrderSide
    from qts.execution import ExecutionAdapter
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import (
        ExecutionActor,
        OrderExecutionRequest,
    )
    from qts.runtime.live_capital import LiveCapitalOrderDecision
    from qts.runtime.mailbox import Mailbox
    from qts.runtime.order_route_metadata import OrderRouteMetadata

    actor = ExecutionActor(
        order_manager_ref=ActorRef(mailbox=Mailbox()),
        execution_adapter=cast(ExecutionAdapter, _ExplodingExecutionAdapter()),
        live_capital_decision=LiveCapitalOrderDecision.disabled(),
    )

    with pytest.raises(PermissionError, match="LIVE_CAPITAL_DISABLED"):
        actor.handle(
            OrderExecutionRequest(
                intent=OrderIntent(
                    order_id=OrderId("ord-live-gate"),
                    instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                    side=OrderSide.BUY,
                    quantity=Decimal("1"),
                    account_id=AccountId("acct-live"),
                ),
                broker_order_id="broker-live-gate",
                market_price=Decimal("101.25"),
                account_id=AccountId("acct-live"),
                strategy_id=StrategyId("strategy-live"),
                route_metadata=OrderRouteMetadata(
                    broker_id=BrokerId("IBKR"),
                    account_id=AccountId("acct-live"),
                    strategy_id=StrategyId("strategy-live"),
                    client_order_id="client-live-gate",
                    correlation_id=CorrelationId("corr-live-gate"),
                ),
            )
        )


class _ExplodingExecutionAdapter:
    def execute_market_order(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("execution adapter must not be called when live gate blocks")

    def cancel_order(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("cancel is not part of this test")


def _live_capital_decision(**overrides: object) -> LiveCapitalOrderDecision:
    from qts.runtime.broker_startup import BrokerRuntimeStartupDecisionStatus
    from qts.runtime.live_capital import LiveCapitalOrderDecision
    from qts.runtime.mode import RuntimeMode
    from qts.runtime.permissions import OrderSubmissionPermission

    values = {
        "runtime_mode": RuntimeMode.LIVE,
        "order_submission_permission": OrderSubmissionPermission.LIVE_ORDERS_ALLOWED,
        "startup_decision_status": BrokerRuntimeStartupDecisionStatus.ALLOW_LIVE,
        "operator_signoff_valid": True,
        "market_data_permission": "live",
        "market_data_freshness": "fresh",
        "reconciliation_status": "clean",
        "kill_switch_active": False,
        "broker_account_kind": "live",
        "broker_account_code": "DU1234567",
        "gateway_port": 4001,
    }
    values.update(overrides)
    return LiveCapitalOrderDecision(**cast(Any, values))
