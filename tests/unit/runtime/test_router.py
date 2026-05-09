from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class _Message:
    account_id: str
    payload: str


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
    router = EventRouter(partition_attr="account_id")
    router.register("acct-001", ref)

    router.route(_Message(account_id="acct-001", payload="a"))
    router.route(_Message(account_id="acct-001", payload="b"))
    ref.process_all()

    assert [message.payload for message in actor.seen] == ["a", "b"]


def test_event_router_unknown_route_is_explicit_error() -> None:
    from qts.runtime.router import EventRouter, RouteNotFoundError

    router = EventRouter(partition_attr="account_id")

    with pytest.raises(RouteNotFoundError, match="no route for key"):
        router.route(_Message(account_id="missing", payload="x"))
