"""Unit tests for actor runtime hardening: supervision, failure events, paths, ask policy."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from unittest.mock import MagicMock

import pytest
from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorAskTimeoutError, ActorUnhandledMessageError
from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_path import ActorPath
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actor_supervisor import ActorSupervisor, SupervisorDecision
from qts.runtime.mailbox import Mailbox

# ---------------------------------------------------------------------------
# ActorFailureEvent
# ---------------------------------------------------------------------------


class TestActorFailureEvent:
    """ActorFailureEvent captures exception info for observability."""

    def test_from_exception_records_type_and_message(self) -> None:
        exc = ValueError("bad fill amount")
        event = ActorFailureEvent.from_exception(actor_name="/account", exception=exc)
        assert event.actor_name == "/account"
        assert event.exception_type == "ValueError"
        assert event.exception_message == "bad fill amount"
        assert event.recoverable is True
        assert event.timestamp is not None

    def test_from_exception_with_non_recoverable(self) -> None:
        exc = RuntimeError("broker disconnected")
        event = ActorFailureEvent.from_exception(
            actor_name="/execution", exception=exc, recoverable=False
        )
        assert event.recoverable is False

    def test_failure_event_is_frozen(self) -> None:
        event = ActorFailureEvent(
            actor_name="test",
            exception_type="ValueError",
            exception_message="x",
            timestamp=datetime.now(tz=UTC),
        )
        with pytest.raises(AttributeError):
            event.actor_name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ActorPath
# ---------------------------------------------------------------------------


class TestActorPath:
    """ActorPath format and child creation."""

    def test_root_path_format(self) -> None:
        path = ActorPath.root("system")
        assert str(path) == "/system"
        assert path.parent is None

    def test_child_path_format(self) -> None:
        root = ActorPath.root("system")
        child = root.child("account")
        assert str(child) == "/system/account"
        assert child.parent == root

    def test_nested_child(self) -> None:
        root = ActorPath.root("system")
        child = root.child("account")
        grandchild = child.child("positions")
        assert str(grandchild) == "/system/account/positions"

    def test_segments(self) -> None:
        root = ActorPath.root("system")
        child = root.child("account")
        assert root.segments == ("system",)
        assert child.segments == ("system", "account")

    def test_path_is_frozen(self) -> None:
        path = ActorPath.root("system")
        with pytest.raises(AttributeError):
            path.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ActorUnhandledMessageError replaces TypeError
# ---------------------------------------------------------------------------


class TestActorUnhandledMessageError:
    """ActorUnhandledMessageError replaces TypeError in actor handle()."""

    def test_account_actor_raises_unhandled_message(self) -> None:
        from qts.runtime.actors.account_actor import AccountActor

        actor = AccountActor(initial_cash={"USD": Decimal("0")})
        with pytest.raises(ActorUnhandledMessageError, match="unsupported account message"):
            actor.handle("bad-message")

    def test_execution_actor_raises_unhandled_message(self) -> None:
        from qts.execution.execution_adapter import ExecutionAdapter
        from qts.runtime.actors.execution_actor import ExecutionActor

        adapter = MagicMock(spec=ExecutionAdapter)
        actor = ExecutionActor(
            order_manager_ref=ActorRef(mailbox=Mailbox()),
            execution_adapter=adapter,
        )
        with pytest.raises(ActorUnhandledMessageError, match="unsupported execution message"):
            actor.handle("bad-message")

    def test_strategy_actor_raises_unhandled_message(self) -> None:
        from qts.runtime.actors.strategy_actor import StrategyActor

        # StrategyActor requires strategy + context + result_ref - minimal mock
        strategy = MagicMock()
        context = MagicMock()
        context.intents = []
        result_ref = ActorRef(mailbox=Mailbox())

        actor = StrategyActor(strategy=strategy, context=context, result_ref=result_ref)
        with pytest.raises(ActorUnhandledMessageError, match="unsupported strategy message"):
            actor.handle("bad-message")

    def test_signal_aggregator_raises_unhandled_message(self) -> None:
        from qts.runtime.actors.signal_aggregator_actor import SignalAggregatorActor

        result_ref = ActorRef(mailbox=Mailbox())
        actor = SignalAggregatorActor(result_ref=result_ref)
        with pytest.raises(
            ActorUnhandledMessageError, match="unsupported signal aggregation message"
        ):
            actor.handle("bad-message")

    def test_order_manager_raises_unhandled_message(self) -> None:
        from qts.runtime.actors.order_manager_actor import OrderManagerActor

        actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=Mailbox()),
            account_ref=ActorRef(mailbox=Mailbox()),
        )
        with pytest.raises(ActorUnhandledMessageError, match="unsupported order manager message"):
            actor.handle("bad-message")

    def test_market_data_actor_raises_unhandled_message(self) -> None:
        from qts.runtime.actors.market_data_actor import MarketDataActor

        actor = MarketDataActor()
        with pytest.raises(ActorUnhandledMessageError, match="unsupported market data message"):
            actor.handle("bad-message")

    def test_unhandled_message_is_not_type_error(self) -> None:
        """ActorUnhandledMessageError is not a TypeError subclass."""
        assert not issubclass(ActorUnhandledMessageError, TypeError)


# ---------------------------------------------------------------------------
# ask_timeout raises ActorAskTimeoutError on timeout
# ---------------------------------------------------------------------------


class TestAskTimeout:
    """ask_timeout raises ActorAskTimeoutError on timeout."""

    def test_ask_with_timeout_raises_actor_ask_timeout_error(self) -> None:
        """When ask_timeout is set and actor never responds, ActorAskTimeoutError is raised."""

        class NoopActor(Actor):
            def handle(self, message: object) -> None:
                # Deliberately do NOT put a response in the response_mailbox
                pass

        class StringQuery:
            def validate_response(self, response: object) -> str:
                if isinstance(response, str):
                    return response
                raise TypeError("expected str response")

        ref = ActorRef(actor=NoopActor(), mailbox=Mailbox())

        with pytest.raises(ActorAskTimeoutError, match="timed out"):
            ref.ask(StringQuery(), ask_timeout=0.05)

    def test_ask_with_none_timeout_blocks_until_response(self) -> None:
        """When ask_timeout is None, ask blocks until the response arrives (synchronous model)."""

        class RespondingActor(Actor):
            def handle(self, message: object) -> None:
                query, response_mailbox = cast(tuple[object, Mailbox], message)
                response_mailbox.put("hello")

        class StringQuery:
            def validate_response(self, response: object) -> str:
                if isinstance(response, str):
                    return response
                raise TypeError("expected str response")

        ref = ActorRef(actor=RespondingActor(), mailbox=Mailbox())
        result = ref.ask(StringQuery(), ask_timeout=None)
        assert result == "hello"

    def test_actor_ask_timeout_error_carries_actor_path(self) -> None:
        """ActorAskTimeoutError message includes the actor path for debugging."""

        class NoopActor(Actor):
            def handle(self, message: object) -> None:
                pass

        class StringQuery:
            def validate_response(self, response: object) -> str:
                return str(response)

        path = ActorPath.root("account")
        ref = ActorRef(actor=NoopActor(), mailbox=Mailbox(), path=path)

        with pytest.raises(ActorAskTimeoutError, match="/account"):
            ref.ask(StringQuery(), ask_timeout=0.05)

    def test_actor_ask_timeout_error_is_not_mailbox_timeout(self) -> None:
        """ActorAskTimeoutError is distinct from MailboxTimeoutError."""
        from qts.runtime.mailbox import MailboxTimeoutError

        assert not issubclass(ActorAskTimeoutError, MailboxTimeoutError)

    def test_ask_default_timeout_is_none(self) -> None:
        """Default ask_timeout is None (blocking wait in synchronous model)."""

        class RespondingActor(Actor):
            def handle(self, message: object) -> None:
                query, response_mailbox = cast(tuple[object, Mailbox], message)
                response_mailbox.put("ok")

        class StringQuery:
            def validate_response(self, response: object) -> str:
                return str(response)

        ref = ActorRef(actor=RespondingActor(), mailbox=Mailbox())
        result = ref.ask(StringQuery())  # no ask_timeout argument
        assert result == "ok"


# ---------------------------------------------------------------------------
# Actor exception does not crash the whole mailbox processing
# ---------------------------------------------------------------------------


class TestFailureIsolation:
    """Actor exception is caught; mailbox continues processing subsequent messages."""

    def test_process_one_catches_exception_and_emits_failure_event(self) -> None:
        """When handle() raises, process_one catches it and emits ActorFailureEvent."""

        class CrashingActor(Actor):
            def __init__(self) -> None:
                self.handled: list[str] = []

            def handle(self, message: object) -> None:
                if message == "crash":
                    raise RuntimeError("boom")
                self.handled.append(str(message))

        failure_events: list[ActorFailureEvent] = []

        def sink(event: ActorFailureEvent) -> None:
            failure_events.append(event)

        actor = CrashingActor()
        mailbox = Mailbox()
        ref = ActorRef(actor=actor, mailbox=mailbox, failure_sink=sink)

        ref.tell("crash")
        result = ref.process_one()

        # process_one still returns True because a message was dequeued
        assert result is True
        # Actor failure event was emitted
        assert len(failure_events) == 1
        assert failure_events[0].exception_type == "RuntimeError"
        assert failure_events[0].exception_message == "boom"
        # Mailbox is empty (message was consumed)
        assert mailbox.empty()

    def test_process_all_continues_after_actor_exception(self) -> None:
        """process_all processes all messages even when some cause exceptions."""

        class PartiallyCrashingActor(Actor):
            def __init__(self) -> None:
                self.handled: list[str] = []

            def handle(self, message: object) -> None:
                if message == "crash":
                    raise ValueError("temporary failure")
                self.handled.append(str(message))

        failure_events: list[ActorFailureEvent] = []

        def sink(event: ActorFailureEvent) -> None:
            failure_events.append(event)

        actor = PartiallyCrashingActor()
        mailbox = Mailbox()
        path = ActorPath.root("test-actor")
        ref = ActorRef(actor=actor, mailbox=mailbox, failure_sink=sink, path=path)

        ref.tell("good-1")
        ref.tell("crash")
        ref.tell("good-2")

        processed = ref.process_all()
        assert processed == 3
        # Two good messages were handled
        assert actor.handled == ["good-1", "good-2"]
        # One failure event was emitted for the crashing message
        assert len(failure_events) == 1
        assert failure_events[0].actor_name == "/test-actor"
        assert failure_events[0].exception_type == "ValueError"
        assert mailbox.empty()

    def test_process_one_without_failure_sink_propagates_exception(self) -> None:
        """Without a failure_sink, exceptions propagate to the caller.

        This ensures silent failure swallowing cannot happen in production
        code paths that don't explicitly configure a failure_sink.
        """

        class CrashingActor(Actor):
            def __init__(self) -> None:
                self.handled: list[str] = []

            def handle(self, message: object) -> None:
                if message == "crash":
                    raise RuntimeError("boom")
                self.handled.append(str(message))

        actor = CrashingActor()
        mailbox = Mailbox()
        # No failure_sink - exception must propagate
        ref = ActorRef(actor=actor, mailbox=mailbox)

        ref.tell("crash")
        with pytest.raises(RuntimeError, match="boom"):
            ref.process_all()

    def test_process_one_without_actor_returns_false(self) -> None:
        """process_one returns False when actor is None (unchanged behavior)."""
        mailbox = Mailbox()
        ref = ActorRef(mailbox=mailbox)
        assert ref.process_one() is False

    def test_process_one_with_empty_mailbox_returns_false(self) -> None:
        """process_one returns False when mailbox is empty (unchanged behavior)."""
        mailbox = Mailbox()
        actor = MagicMock(spec=Actor)
        ref = ActorRef(actor=actor, mailbox=mailbox)
        assert ref.process_one() is False


# ---------------------------------------------------------------------------
# ActorSupervisor
# ---------------------------------------------------------------------------


class TestActorSupervisor:
    """Supervisor registers and handles failure events."""

    def test_supervise_registers_actor(self) -> None:
        supervisor = ActorSupervisor()
        mailbox = Mailbox()
        actor_ref = ActorRef(mailbox=mailbox)
        path = ActorPath.root("account")
        supervisor.supervise(actor_ref, path=path)
        # Actor is registered
        assert path in supervisor._registered

    def test_handle_failure_logs_and_records_event(self) -> None:
        supervisor = ActorSupervisor()
        event = ActorFailureEvent.from_exception(
            actor_name="/account",
            exception=ValueError("bad fill"),
        )
        supervisor.handle_failure(event)
        assert len(supervisor.failure_events) == 1
        assert supervisor.failure_events[0] == event

    def test_handle_failure_marks_actor_as_failed(self) -> None:
        supervisor = ActorSupervisor()
        path = ActorPath.root("account")
        actor_ref = ActorRef(mailbox=Mailbox())
        supervisor.supervise(actor_ref, path=path)

        event = ActorFailureEvent.from_exception(
            actor_name="/account",
            exception=RuntimeError("disconnect"),
        )
        supervisor.handle_failure(event)
        assert supervisor.is_failed(path)
        assert path in supervisor.failed_paths

    def test_supervisor_on_failure_callback(self) -> None:
        callback_events: list[ActorFailureEvent] = []
        supervisor = ActorSupervisor(on_failure=lambda e: callback_events.append(e))

        event = ActorFailureEvent.from_exception(
            actor_name="/execution",
            exception=ConnectionError("broker down"),
        )
        supervisor.handle_failure(event)
        assert len(callback_events) == 1
        assert callback_events[0] == event

    def test_supervisor_integrated_with_actor_ref_failure_sink(self) -> None:
        """End-to-end: ActorRef failure_sink wired to supervisor."""

        class CrashingActor(Actor):
            def handle(self, message: object) -> None:
                raise RuntimeError("critical failure")

        supervisor = ActorSupervisor()
        path = ActorPath.root("execution")
        mailbox = Mailbox()
        actor = CrashingActor()
        actor_ref = ActorRef(
            actor=actor,
            mailbox=mailbox,
            path=path,
            failure_sink=supervisor.handle_failure,
        )
        supervisor.supervise(actor_ref, path=path)

        actor_ref.tell("trigger-crash")
        actor_ref.process_all()

        assert len(supervisor.failure_events) == 1
        assert supervisor.is_failed(path)
        assert supervisor.failure_events[0].actor_name == "/execution"
        assert supervisor.failure_events[0].exception_type == "RuntimeError"

    def test_supervisor_decision_enum(self) -> None:
        """SupervisorDecision enum exists for future restart policy."""
        assert SupervisorDecision.LOG is not None
        assert SupervisorDecision.STOP is not None
        assert SupervisorDecision.RESTART is not None


# ---------------------------------------------------------------------------
# Backward compatibility: existing actor tests still pass
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Existing usage patterns continue to work with no changes."""

    def test_actor_ref_tell_and_process_all_work_without_path_or_sink(self) -> None:
        """ActorRef without path or failure_sink works as before."""

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

    def test_actor_ref_ask_validates_response_type(self) -> None:
        """ask() still validates response types (original test behavior)."""

        class StringQuery:
            def validate_response(self, response: object) -> str:
                if not isinstance(response, str):
                    raise TypeError("expected str response")
                return response

        class BadActor(Actor):
            def handle(self, message: object) -> None:
                query, response_mailbox = cast(tuple[object, Mailbox], message)
                response_mailbox.put(123)

        ref = ActorRef(actor=BadActor(), mailbox=Mailbox())

        with pytest.raises(TypeError, match="expected str response"):
            ref.ask(StringQuery())

    def test_actor_ref_default_path_is_none(self) -> None:
        """ActorRef default path is None (backward compatible)."""
        mailbox = Mailbox()
        ref = ActorRef(mailbox=mailbox)
        assert ref.path is None

    def test_actor_ref_default_failure_sink_is_none(self) -> None:
        """ActorRef default failure_sink is None (backward compatible)."""
        mailbox = Mailbox()
        ref = ActorRef(mailbox=mailbox)
        assert ref.failure_sink is None
