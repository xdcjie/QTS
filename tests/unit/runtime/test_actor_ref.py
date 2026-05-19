from __future__ import annotations

from typing import cast

import pytest


def test_actor_ref_ask_validates_response_type() -> None:
    from qts.runtime.actor import Actor
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.mailbox import Mailbox

    class StringQuery:
        def validate_response(self, response: object) -> str:
            if not isinstance(response, str):
                raise TypeError("expected str response")
            return response

    class BadActor(Actor):
        def handle(self, message: object) -> None:
            query, response_mailbox = cast(tuple[object, Mailbox], message)
            _ = query
            response_mailbox.put(123)

    ref = ActorRef(actor=BadActor(), mailbox=Mailbox())

    with pytest.raises(TypeError, match="expected str response"):
        ref.ask(StringQuery())
