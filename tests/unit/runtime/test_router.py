from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest


@dataclass(frozen=True)
class _Message:
    account_id: str
    payload: str


@dataclass(frozen=True)
class _MarketDataRouteMessage:
    market_data_source_id: str
    payload: object


@dataclass(frozen=True)
class _ExecutionRouteMessage:
    account_id: str
    payload: object


def test_event_router_routes_by_configured_key_deterministically() -> None:
    from qts.runtime.actor import Actor
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.mailbox import Mailbox
    from qts.runtime.router import EventRouter

    class RecordingActor(Actor):
        def __init__(self) -> None:
            self.seen: list[_Message] = []

        def handle(self, message: object) -> None:
            assert isinstance(message, _Message)
            self.seen.append(message)

    actor = RecordingActor()
    ref = ActorRef(actor=actor, mailbox=Mailbox())
    router = EventRouter(key_for=lambda message: cast(_Message, message).account_id)
    router.register("acct-001", ref)

    router.route(_Message(account_id="acct-001", payload="a"))
    router.route(_Message(account_id="acct-001", payload="b"))
    ref.process_all()

    assert [message.payload for message in actor.seen] == ["a", "b"]


def test_event_router_unknown_route_is_explicit_error() -> None:
    from qts.runtime.router import EventRouter, RouteNotFoundError

    router = EventRouter(key_for=lambda message: cast(_Message, message).account_id)

    with pytest.raises(RouteNotFoundError, match="no route for key"):
        router.route(_Message(account_id="missing", payload="x"))


def test_event_router_routes_market_data_and_execution_messages_to_separate_actor_types() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.market_data import Tick
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.execution_actor import ExecutionActor, OrderExecutionRequest
    from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
    from qts.runtime.mailbox import Mailbox
    from qts.runtime.router import EventRouter

    market_data_mailbox = Mailbox()
    execution_mailbox = Mailbox()
    order_manager_mailbox = Mailbox()
    market_data_ref = ActorRef(actor=MarketDataActor(), mailbox=market_data_mailbox)
    execution_ref = ActorRef(
        actor=ExecutionActor(order_manager_ref=ActorRef(mailbox=order_manager_mailbox)),
        mailbox=execution_mailbox,
    )
    market_data_router = EventRouter(
        key_for=lambda message: cast(_MarketDataRouteMessage, message).market_data_source_id
    )
    execution_router = EventRouter(
        key_for=lambda message: cast(_ExecutionRouteMessage, message).account_id
    )
    market_data_router.register("ibkr-paper-md", market_data_ref)
    execution_router.register("DU1234567", execution_ref)

    market_data_message = _MarketDataRouteMessage(
        market_data_source_id="ibkr-paper-md",
        payload=MarketDataEvent(
            payload=Tick(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
                price=Decimal("100"),
                size=Decimal("1"),
            )
        ),
    )
    execution_message = _ExecutionRouteMessage(
        account_id="DU1234567",
        payload=OrderExecutionRequest(
            intent=OrderIntent(
                order_id=OrderId("ord-001"),
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                side=OrderSide.BUY,
                quantity=Decimal("1"),
            ),
            broker_order_id="ibkr-001",
            market_price=Decimal("100"),
        ),
    )

    market_data_router.route(market_data_message)
    execution_router.route(execution_message)

    assert market_data_mailbox.get() == market_data_message
    assert execution_mailbox.get() == execution_message
    assert order_manager_mailbox.empty()
