"""Anchor tests for actor ask policy and failure event emission.

These tests verify durable invariants of the actor runtime hardening:

1. ask() in live-critical paths has a bounded timeout; unbounded waits are rejected
2. Actor failure emits structured ActorFailureEvent, not silent crash
3. ActorUnhandledMessageError replaces TypeError in message dispatch
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorAskTimeoutError, ActorUnhandledMessageError
from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_path import ActorPath
from qts.runtime.actor_ref import DEFAULT_ACTOR_ASK_TIMEOUT_SECONDS, ActorRef
from qts.runtime.actor_supervisor import ActorSupervisor
from qts.runtime.mailbox import Mailbox

# ---------------------------------------------------------------------------
# Anchor: ask() in live-critical path has bounded timeout
# ---------------------------------------------------------------------------


class TestAskPolicyAnchor:
    """Anchor: ask() supports bounded timeout for live-critical broker callbacks."""

    def test_ask_timeout_raises_actor_ask_timeout_error_on_expiry(self) -> None:
        """When ask_timeout is set and no response arrives, ActorAskTimeoutError
        is raised instead of blocking indefinitely.  This is the gate that
        prevents unbounded synchronous drain in live-critical broker
        callbacks."""

        class SilentActor(Actor):
            def handle(self, message: object) -> None:
                # Deliberately never respond
                pass

        class StringQuery:
            def validate_response(self, response: object) -> str:
                return str(response)

        ref = ActorRef(actor=SilentActor(), mailbox=Mailbox())

        with pytest.raises(ActorAskTimeoutError):
            ref.ask(StringQuery(), ask_timeout=0.05)

    def test_ask_timeout_none_is_rejected(self) -> None:
        """ask_timeout=None would create an unbounded actor wait, so the
        runtime rejects it before the message reaches the actor."""

        class StringQuery:
            def validate_response(self, response: object) -> str:
                return str(response)

        class SilentActor(Actor):
            def handle(self, message: object) -> None:
                pass

        ref = ActorRef(actor=SilentActor(), mailbox=Mailbox())

        with pytest.raises(ValueError, match="ask_timeout=None is not allowed"):
            ref.ask(StringQuery(), ask_timeout=None)

    def test_actor_ask_timeout_error_is_distinct_from_mailbox_timeout(self) -> None:
        """ActorAskTimeoutError is a domain-specific error, not a
        MailboxTimeoutError.  Callers in live-critical paths catch
        ActorAskTimeoutError specifically."""
        from qts.runtime.mailbox import MailboxTimeoutError

        # ActorAskTimeoutError is not a subclass of MailboxTimeoutError
        assert not issubclass(ActorAskTimeoutError, MailboxTimeoutError)
        # ActorAskTimeoutError is not a subclass of TimeoutError
        assert not issubclass(ActorAskTimeoutError, TimeoutError)

    def test_ask_timeout_parameter_exists_in_actor_ref(self) -> None:
        """ActorRef.ask() has an ask_timeout parameter (float | None).
        This anchor ensures the parameter is part of the public API."""
        import inspect

        sig = inspect.signature(ActorRef.ask)
        assert "ask_timeout" in sig.parameters
        param = sig.parameters["ask_timeout"]
        assert param.default == DEFAULT_ACTOR_ASK_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# Anchor: actor failure emits structured ActorFailureEvent, not silent crash
# ---------------------------------------------------------------------------


class TestActorFailureEventAnchor:
    """Anchor: actor failures emit structured ActorFailureEvent, not
    silent crash.  The system does not crash on a single actor failure."""

    def test_process_one_emits_failure_event_on_exception(self) -> None:
        """When actor.handle() raises, process_one catches the exception
        and emits an ActorFailureEvent to the configured failure_sink.
        This is the gate ensuring failures are observable, not silent."""

        class CrashingActor(Actor):
            def handle(self, message: object) -> None:
                raise ValueError("bad state")

        events: list[ActorFailureEvent] = []
        path = ActorPath.root("risk-engine")

        def sink(event: ActorFailureEvent) -> None:
            events.append(event)

        ref = ActorRef(
            actor=CrashingActor(),
            mailbox=Mailbox(),
            path=path,
            failure_sink=sink,
        )
        ref.tell("trigger")
        ref.process_one()

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, ActorFailureEvent)
        assert event.actor_name == "/risk-engine"
        assert event.exception_type == "ValueError"
        assert event.exception_message == "bad state"

    def test_actor_failure_event_is_frozen_dataclass(self) -> None:
        """ActorFailureEvent is frozen to prevent mutation after emission.
        This ensures failure events are immutable audit records."""
        event = ActorFailureEvent(
            actor_name="test",
            exception_type="ValueError",
            exception_message="x",
            timestamp=datetime.now(tz=UTC),
        )
        with pytest.raises(AttributeError):
            event.actor_name = "mutated"  # type: ignore[misc]

    def test_actor_failure_does_not_crash_mailbox_processing(self) -> None:
        """A single actor failure does not crash the entire mailbox
        processing loop.  Subsequent messages continue to be processed.
        This is the graceful-degradation gate."""

        class PartiallyCrashingActor(Actor):
            def __init__(self) -> None:
                self.seen: list[str] = []

            def handle(self, message: object) -> None:
                if message == "crash":
                    raise RuntimeError("transient failure")
                self.seen.append(str(message))

        events: list[ActorFailureEvent] = []

        def sink(event: ActorFailureEvent) -> None:
            events.append(event)

        actor = PartiallyCrashingActor()
        ref = ActorRef(
            actor=actor,
            mailbox=Mailbox(),
            path=ActorPath.root("account"),
            failure_sink=sink,
        )
        ref.tell("good-before")
        ref.tell("crash")
        ref.tell("good-after")

        ref.process_all()

        # Good messages were handled despite the crash
        assert actor.seen == ["good-before", "good-after"]
        # Failure event was emitted for the crash
        assert len(events) == 1
        assert events[0].exception_type == "RuntimeError"

    def test_supervisor_records_and_classifies_failure(self) -> None:
        """ActorSupervisor records failures and tracks failed actors.
        This is the observability gate for production monitoring."""
        supervisor = ActorSupervisor()
        path = ActorPath.root("execution")
        ref = ActorRef(mailbox=Mailbox(), path=path)
        supervisor.supervise(ref, path=path)

        event = ActorFailureEvent.from_exception(
            actor_name="/execution",
            exception=ValueError("bad fill"),
        )
        supervisor.handle_failure(event)

        assert supervisor.is_failed(path)
        assert len(supervisor.failure_events) == 1
        assert supervisor.failure_events[0].exception_type == "ValueError"


# ---------------------------------------------------------------------------
# Anchor: ActorUnhandledMessageError replaces TypeError in dispatch
# ---------------------------------------------------------------------------


class TestUnhandledMessageErrorAnchor:
    """Anchor: ActorUnhandledMessageError is the canonical dispatch-error
    type, distinct from TypeError.  This makes message-dispatch failures
    distinguishable from type-validation failures."""

    def test_unhandled_message_error_is_not_type_error(self) -> None:
        """ActorUnhandledMessageError is not a TypeError subclass, so
        catching TypeError does not accidentally catch dispatch errors."""
        assert not issubclass(ActorUnhandledMessageError, TypeError)

    def test_actors_use_unhandled_message_error_not_type_error(self) -> None:
        """All actors raise ActorUnhandledMessageError, not TypeError,
        for unhandled messages.  This anchor scans the known actors."""
        from decimal import Decimal
        from unittest.mock import MagicMock

        from qts.execution.execution_adapter import ExecutionAdapter
        from qts.runtime.actors.account_actor import AccountActor
        from qts.runtime.actors.execution_actor import ExecutionActor
        from qts.runtime.actors.market_data_actor import MarketDataActor
        from qts.runtime.actors.order_manager_actor import OrderManagerActor
        from qts.runtime.actors.signal_aggregator_actor import SignalAggregatorActor
        from qts.runtime.actors.strategy_actor import StrategyActor

        # AccountActor
        account_actor = AccountActor(initial_cash={"USD": Decimal("0")})
        with pytest.raises(ActorUnhandledMessageError):
            account_actor.handle("unknown")

        # ExecutionActor
        adapter = MagicMock(spec=ExecutionAdapter)
        execution_actor = ExecutionActor(
            order_manager_ref=ActorRef(mailbox=Mailbox()),
            execution_adapter=adapter,
        )
        with pytest.raises(ActorUnhandledMessageError):
            execution_actor.handle("unknown")

        # MarketDataActor
        market_data_actor = MarketDataActor()
        with pytest.raises(ActorUnhandledMessageError):
            market_data_actor.handle("unknown")

        # OrderManagerActor
        order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=Mailbox()),
            account_ref=ActorRef(mailbox=Mailbox()),
        )
        with pytest.raises(ActorUnhandledMessageError):
            order_manager_actor.handle("unknown")

        # SignalAggregatorActor
        result_ref = ActorRef(mailbox=Mailbox())
        signal_actor = SignalAggregatorActor(result_ref=result_ref)
        with pytest.raises(ActorUnhandledMessageError):
            signal_actor.handle("unknown")

        # StrategyActor
        strategy = MagicMock()
        context = MagicMock()
        context.intents = []
        strategy_actor = StrategyActor(
            strategy=strategy, context=context, result_ref=ActorRef(mailbox=Mailbox())
        )
        with pytest.raises(ActorUnhandledMessageError):
            strategy_actor.handle("unknown")
