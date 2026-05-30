from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from qts.core.ids import AccountId, CorrelationId, StrategyId
    from qts.runtime.order_route_metadata import OrderRouteMetadata


def test_order_manager_actor_sends_broker_request_and_emits_validated_fill() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import ApplyFill
    from qts.runtime.actors.execution_actor import OrderExecutionRequest
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    execution = Mailbox()
    account = Mailbox()
    account_id = AccountId("acct-a")
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=account),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        account_id=account_id,
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
            account_id=account_id,
            strategy_id=StrategyId("strategy-a"),
            route_metadata=_route_metadata(
                account_id=account_id,
                strategy_id=StrategyId("strategy-a"),
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
            ),
        )
    )
    execution_request = execution.get()
    assert isinstance(execution_request, OrderExecutionRequest)
    assert execution_request.intent == intent
    assert execution_request.account_id == account_id
    assert execution_request.strategy_id == StrategyId("strategy-a")
    assert execution_request.route_metadata.client_order_id == "client-001"
    assert execution_request.route_metadata.correlation_id == CorrelationId("corr-001")

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
    assert fill_message.fill.account_id == account_id
    assert fill_message.fill.quantity == Decimal("10")
    assert actor.get_order(intent.order_id).broker_order_id == "broker-001"


def test_order_manager_actor_does_not_send_risk_rejected_order_to_execution() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    execution = Mailbox()
    account_id = AccountId("acct-a")
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-rejected"),
        account_id=account_id,
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
                account_id=account_id,
                strategy_id=StrategyId("strategy-a"),
                route_metadata=_route_metadata(
                    account_id=account_id,
                    strategy_id=StrategyId("strategy-a"),
                    client_order_id="client-001",
                    correlation_id=CorrelationId("corr-001"),
                ),
            )
        )

    assert execution.empty()


def test_order_for_account_a_routes_to_account_a_execution_actor() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import OrderExecutionRequest
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    execution = Mailbox()
    account_id = AccountId("acct-a")
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
    )

    actor.handle(
        SubmitOrder(
            intent=OrderIntent(
                order_id=OrderId("ord-001"),
                account_id=account_id,
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("10"),
            ),
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-001",
            market_price=Decimal("101"),
            account_id=account_id,
            strategy_id=StrategyId("strategy-a"),
            route_metadata=_route_metadata(
                account_id=account_id,
                strategy_id=StrategyId("strategy-a"),
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
            ),
        )
    )

    execution_request = execution.get()
    assert isinstance(execution_request, OrderExecutionRequest)
    assert execution_request.account_id == account_id


def test_order_for_wrong_account_is_rejected() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    actor = OrderManagerActor(
        account_id=AccountId("acct-a"),
        execution_ref=ActorRef(mailbox=Mailbox()),
        account_ref=ActorRef(mailbox=Mailbox()),
    )

    with pytest.raises(ValueError, match="order account_id"):
        actor.handle(
            SubmitOrder(
                intent=OrderIntent(
                    order_id=OrderId("ord-001"),
                    account_id=AccountId("acct-b"),
                    instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                    side=OrderSide.BUY,
                    quantity=Decimal("10"),
                ),
                risk_decision=RiskDecision.approve(),
                broker_order_id="broker-001",
                market_price=Decimal("101"),
                account_id=AccountId("acct-b"),
                strategy_id=StrategyId("strategy-a"),
                route_metadata=_route_metadata(
                    account_id=AccountId("acct-b"),
                    strategy_id=StrategyId("strategy-a"),
                    client_order_id="client-001",
                    correlation_id=CorrelationId("corr-001"),
                ),
            )
        )


def test_cancel_for_account_a_cannot_cancel_account_b_order() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        CancelIntent,
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.order_manager_actor import CancelOrder, OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    execution = Mailbox()
    account_id = AccountId("acct-b")
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    order_id = OrderId("ord-001")
    actor.handle(
        SubmitOrder(
            intent=OrderIntent(
                order_id=order_id,
                account_id=account_id,
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("10"),
            ),
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-001",
            market_price=Decimal("101"),
            account_id=account_id,
            strategy_id=StrategyId("strategy-b"),
            route_metadata=_route_metadata(
                account_id=account_id,
                strategy_id=StrategyId("strategy-b"),
                client_order_id="client-b",
                correlation_id=CorrelationId("corr-b"),
            ),
        )
    )
    assert execution.get() is not None

    with pytest.raises(ValueError, match="cancel account_id"):
        actor.handle(
            CancelOrder(
                intent=CancelIntent(order_id=order_id),
                account_id=AccountId("acct-a"),
                strategy_id=StrategyId("strategy-b"),
                route_metadata=_route_metadata(
                    account_id=AccountId("acct-a"),
                    strategy_id=StrategyId("strategy-b"),
                    client_order_id="client-b",
                    correlation_id=CorrelationId("corr-b"),
                ),
            )
        )

    assert execution.empty()


def test_order_route_metadata_is_preserved_across_submit_cancel_replace_and_fill() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        CancelIntent,
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderSide,
        ReplaceIntent,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import ApplyFill
    from qts.runtime.actors.execution_actor import OrderCancelRequest, OrderExecutionRequest
    from qts.runtime.actors.order_manager_actor import (
        CancelOrder,
        OrderManagerActor,
        ReplaceOrder,
        SubmitOrder,
    )
    from qts.runtime.mailbox import Mailbox
    from qts.runtime.order_route_metadata import OrderRouteMetadata

    broker_id = BrokerId("broker-route")
    account_a = AccountId("acct-a")
    account_b = AccountId("acct-b")
    strategy_a = StrategyId("strategy-a")
    strategy_b = StrategyId("strategy-b")
    order_id_a = OrderId("ord-a")
    order_id_b = OrderId("ord-b")
    metadata_a = OrderRouteMetadata(
        broker_id=broker_id,
        account_id=account_a,
        strategy_id=strategy_a,
        client_order_id="client-a",
        correlation_id=CorrelationId("corr-a"),
    )
    metadata_b = OrderRouteMetadata(
        broker_id=broker_id,
        account_id=account_b,
        strategy_id=strategy_b,
        client_order_id="client-b",
        correlation_id=CorrelationId("corr-b"),
    )
    execution_a = Mailbox()
    execution_b = Mailbox()
    account_mailbox_a = Mailbox()
    account_mailbox_b = Mailbox()
    actor_a = OrderManagerActor(
        account_id=account_a,
        execution_ref=ActorRef(mailbox=execution_a),
        account_ref=ActorRef(mailbox=account_mailbox_a),
    )
    actor_b = OrderManagerActor(
        account_id=account_b,
        execution_ref=ActorRef(mailbox=execution_b),
        account_ref=ActorRef(mailbox=account_mailbox_b),
    )
    intent_a = OrderIntent(
        order_id=order_id_a,
        account_id=account_a,
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )
    intent_b = OrderIntent(
        order_id=order_id_b,
        account_id=account_b,
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("20"),
    )

    actor_a.handle(
        SubmitOrder(
            intent=intent_a,
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-order-a",
            market_price=Decimal("101"),
            account_id=account_a,
            strategy_id=strategy_a,
            route_metadata=metadata_a,
        )
    )
    actor_b.handle(
        SubmitOrder(
            intent=intent_b,
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-order-b",
            market_price=Decimal("102"),
            account_id=account_b,
            strategy_id=strategy_b,
            route_metadata=metadata_b,
        )
    )

    submit_a = execution_a.get()
    submit_b = execution_b.get()
    assert isinstance(submit_a, OrderExecutionRequest)
    assert isinstance(submit_b, OrderExecutionRequest)
    assert submit_a.route_metadata == metadata_a
    assert submit_b.route_metadata == metadata_b
    assert actor_a.route_metadata(order_id_a) == metadata_a
    assert actor_b.route_metadata(order_id_b) == metadata_b

    actor_a.handle(
        CancelOrder(
            intent=CancelIntent(order_id=order_id_a),
            account_id=account_a,
            strategy_id=strategy_a,
            route_metadata=metadata_a,
        )
    )

    cancel_a = execution_a.get()
    assert isinstance(cancel_a, OrderCancelRequest)
    assert cancel_a.order_id == order_id_a
    assert cancel_a.route_metadata == metadata_a
    assert execution_b.empty()

    actor_a.handle(
        ReplaceOrder(
            intent=ReplaceIntent(order_id=order_id_a, new_quantity=Decimal("12")),
            risk_decision=RiskDecision.approve(),
            account_id=account_a,
            strategy_id=strategy_a,
            route_metadata=metadata_a,
        )
    )
    assert actor_a.replace_rejections[-1].order_id == order_id_a
    assert actor_a.replace_rejections[-1].reason_code == "REPLACE_NOT_SUPPORTED"
    assert actor_a.route_metadata(order_id_a) == metadata_a

    actor_a.handle(
        ExecutionReport(
            report_id="rpt-a",
            broker_order_id="broker-order-a",
            status=ExecutionReportStatus.FILLED,
            filled_quantity=Decimal("10"),
            fill_price=Decimal("101"),
            fill_id="fill-a",
        )
    )

    fill_message = account_mailbox_a.get()
    assert isinstance(fill_message, ApplyFill)
    assert fill_message.fill.account_id == account_a
    assert actor_a.route_metadata(fill_message.fill.order_id).correlation_id == CorrelationId(
        "corr-a"
    )
    assert account_mailbox_b.empty()


def test_cancel_route_metadata_mismatch_fails_fast_before_execution() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        CancelIntent,
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.order_manager_actor import (
        CancelOrder,
        OrderManagerActor,
        SubmitOrder,
    )
    from qts.runtime.mailbox import Mailbox
    from qts.runtime.order_route_metadata import OrderRouteMetadata

    account_id = AccountId("acct-a")
    strategy_id = StrategyId("strategy-a")
    order_id = OrderId("ord-a")
    original_metadata = OrderRouteMetadata(
        broker_id=BrokerId("broker-route"),
        account_id=account_id,
        strategy_id=strategy_id,
        client_order_id="client-a",
        correlation_id=CorrelationId("corr-a"),
    )
    wrong_metadata = OrderRouteMetadata(
        broker_id=BrokerId("broker-route-other"),
        account_id=account_id,
        strategy_id=strategy_id,
        client_order_id="client-a",
        correlation_id=CorrelationId("corr-a"),
    )
    execution = Mailbox()
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    actor.handle(
        SubmitOrder(
            intent=OrderIntent(
                order_id=order_id,
                account_id=account_id,
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("10"),
            ),
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-order-a",
            market_price=Decimal("101"),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=original_metadata,
        )
    )
    assert execution.get() is not None

    with pytest.raises(ValueError, match="cancel route metadata"):
        actor.handle(
            CancelOrder(
                intent=CancelIntent(order_id=order_id),
                account_id=account_id,
                strategy_id=strategy_id,
                route_metadata=wrong_metadata,
            )
        )

    assert execution.empty()


def test_order_route_metadata_round_trips_for_recovery() -> None:
    from qts.core.ids import AccountId, BrokerId, CorrelationId, StrategyId
    from qts.runtime.order_route_metadata import OrderRouteMetadata

    metadata = OrderRouteMetadata(
        broker_id=BrokerId("broker-route"),
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strategy-a"),
        client_order_id="client-a",
        correlation_id=CorrelationId("corr-a"),
    )

    restored = OrderRouteMetadata.from_payload(metadata.to_payload())

    assert restored == metadata


def test_replace_order_returns_structured_rejection_not_not_implemented_error() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        OrderIntent,
        OrderSide,
        ReplaceIntent,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, ReplaceOrder, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    account_id = AccountId("acct-a")
    strategy_id = StrategyId("strategy-a")
    order_id = OrderId("ord-replace-reject")
    execution = Mailbox()
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    actor.handle(
        SubmitOrder(
            intent=OrderIntent(
                order_id=order_id,
                account_id=account_id,
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("10"),
            ),
            risk_decision=RiskDecision.approve(),
            broker_order_id="broker-replace-reject",
            market_price=Decimal("101"),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=_route_metadata(
                account_id=account_id,
                strategy_id=strategy_id,
                client_order_id="client-replace-reject",
                correlation_id=CorrelationId("corr-replace-reject"),
            ),
        )
    )
    assert execution.get() is not None

    actor.handle(
        ReplaceOrder(
            intent=ReplaceIntent(order_id=order_id, new_quantity=Decimal("20")),
            risk_decision=RiskDecision.approve(),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=_route_metadata(
                account_id=account_id,
                strategy_id=strategy_id,
                client_order_id="client-replace-reject",
                correlation_id=CorrelationId("corr-replace-reject"),
            ),
        )
    )

    rejection = actor.replace_rejections[-1]
    assert rejection.order_id == order_id
    assert rejection.reason_code == "REPLACE_NOT_SUPPORTED"

    order = actor.get_order(order_id)
    assert order.intent.quantity == Decimal("10"), (
        "order quantity must remain unchanged after rejected replace"
    )


def test_order_route_metadata_references_signal_aggregation_decision() -> None:
    from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import (
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
    from qts.runtime.mailbox import Mailbox

    execution = Mailbox()
    account_id = AccountId("acct-a")
    contributing_strategy_ids = (
        StrategyId("strategy-a"),
        StrategyId("strategy-b"),
    )
    aggregation_decision_id = "sigagg-abc123"
    actor = OrderManagerActor(
        account_id=account_id,
        execution_ref=ActorRef(mailbox=execution),
        account_ref=ActorRef(mailbox=Mailbox()),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-aggregation"),
        account_id=account_id,
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    actor.handle(
        SubmitOrder(
            intent=intent,
            risk_decision=RiskDecision.approve(
                contributing_strategy_ids=contributing_strategy_ids,
                aggregation_decision_id=aggregation_decision_id,
            ),
            broker_order_id="broker-aggregation",
            market_price=Decimal("101"),
            account_id=account_id,
            strategy_id=StrategyId("strategy-a"),
            route_metadata=_route_metadata(
                account_id=account_id,
                strategy_id=StrategyId("strategy-a"),
                client_order_id="client-aggregation",
                correlation_id=CorrelationId("corr-aggregation"),
                contributing_strategy_ids=contributing_strategy_ids,
                aggregation_decision_id=aggregation_decision_id,
            ),
        )
    )

    metadata = actor.route_metadata(intent.order_id)
    assert metadata.contributing_strategy_ids == contributing_strategy_ids
    assert metadata.aggregation_decision_id == aggregation_decision_id


def _route_metadata(
    *,
    account_id: AccountId,
    strategy_id: StrategyId,
    client_order_id: str,
    correlation_id: CorrelationId,
    contributing_strategy_ids: tuple[StrategyId, ...] = (),
    aggregation_decision_id: str | None = None,
) -> OrderRouteMetadata:
    from qts.core.ids import BrokerId
    from qts.runtime.order_route_metadata import OrderRouteMetadata

    return OrderRouteMetadata(
        broker_id=BrokerId("broker-route"),
        account_id=account_id,
        strategy_id=strategy_id,
        client_order_id=client_order_id,
        correlation_id=correlation_id,
        contributing_strategy_ids=contributing_strategy_ids,
        aggregation_decision_id=aggregation_decision_id,
    )
