"""Actor ask is bounded and returns supervised actor failures to callers."""

from __future__ import annotations

import pytest
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorAskFailed
from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_ref import ActorRef
from qts.runtime.mailbox import Mailbox


class _StringQuery:
    def validate_response(self, response: object) -> str:
        if not isinstance(response, str):
            raise TypeError("expected str")
        return response


class _FailingActor(Actor):
    def handle(self, message: object) -> None:
        raise RuntimeError(f"boom: {type(message).__name__}")


def test_ask_returns_failure_response_when_supervised_actor_fails() -> None:
    failures: list[ActorFailureEvent] = []
    ref: ActorRef = ActorRef(
        actor=_FailingActor(),
        mailbox=Mailbox(),
        failure_sink=failures.append,
    )

    with pytest.raises(ActorAskFailed, match="boom"):
        ref.ask(_StringQuery())

    assert len(failures) == 1


def test_ask_rejects_unbounded_timeout() -> None:
    ref: ActorRef = ActorRef(mailbox=Mailbox())

    with pytest.raises(ValueError, match="ask_timeout=None is not allowed"):
        ref.ask(_StringQuery(), ask_timeout=None)
