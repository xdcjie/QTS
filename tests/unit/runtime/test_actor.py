from __future__ import annotations


def test_actor_ref_tell_enqueues_and_actor_processes_serially() -> None:
    from qts.runtime.actor import Actor
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.mailbox import Mailbox

    class RecordingActor(Actor):
        def __init__(self) -> None:
            self.seen: list[str] = []

        def handle(self, message: object) -> None:
            self.seen.append(str(message))

    actor = RecordingActor()
    mailbox = Mailbox()
    ref = ActorRef(actor=actor, mailbox=mailbox)

    ref.tell("first")
    ref.tell("second")

    assert mailbox.size == 2
    assert ref.process_all() == 2
    assert actor.seen == ["first", "second"]
    assert mailbox.size == 0
