"""Actor supervisor: restart/degrade decisions and failure observability."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import Enum, auto
from logging import getLogger
from typing import TYPE_CHECKING, Protocol

from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_path import ActorPath
from qts.runtime.actor_policies import (
    AskContextPolicy,
    MailboxDrainPolicy,
    RestartPolicy,
)
from qts.runtime.actor_ref import ActorRef

if TYPE_CHECKING:
    from qts.core.ids import AccountId
    from qts.runtime.broker_runtime_topology import AccountRuntimePartition
    from qts.runtime.state import RuntimeSessionState

logger = getLogger(__name__)


class SupervisorDecision(Enum):
    """Decision taken by the supervisor on actor failure."""

    LOG = auto()
    STOP = auto()
    RESTART = auto()
    DEGRADE = auto()
    ESCALATE = auto()


class _RuntimeSupervisionSessionPort(Protocol):
    """Runtime-session surface required by actor supervision."""

    @property
    def state(self) -> RuntimeSessionState:
        """Return the current runtime lifecycle state."""
        ...

    def supervised_actor_partitions(
        self,
    ) -> tuple[tuple[AccountId | None, AccountRuntimePartition], ...]:
        """Return account partitions whose actors should be supervised."""
        ...

    def write_supervisor_event(self, kind: str, payload: Mapping[str, object]) -> None:
        """Record a runtime supervision event."""
        ...

    def degrade(self) -> RuntimeSessionState:
        """Degrade the session after unrecoverable actor failure."""
        ...


class ActorSupervisor:
    """Supervisor that registers actors and decides restart vs. degrade on failure.

    The supervisor receives :class:`ActorFailureEvent` via its
    :meth:`handle_failure` method (typically wired as a ``failure_sink`` on
    :class:`ActorRef`).  It records the failure, applies a bounded
    :class:`~qts.runtime.actor_policies.RestartPolicy`, and returns a
    :class:`SupervisorDecision`:

    * ``RESTART`` for a recoverable failure whose actor still has restart
      budget within the policy window.  On restart the failed actor's mailbox
      is handled per the configured
      :class:`~qts.runtime.actor_policies.MailboxDrainPolicy`.
    * ``DEGRADE`` once the restart budget is exhausted, or for a
      non-recoverable failure.  Callers (e.g. ``RuntimeSession``) map this onto
      a session degrade so the system stops accepting new work while keeping
      observability alive.

    The decision is deterministic given the recorded failure history, so it is
    fully unit-testable.
    """

    def __init__(
        self,
        *,
        restart_policy: RestartPolicy | None = None,
        mailbox_drain_policy: MailboxDrainPolicy | None = None,
        ask_context_policy: AskContextPolicy | None = None,
        on_failure: Callable[[ActorFailureEvent], None] | None = None,
        on_decision: Callable[[ActorFailureEvent, SupervisorDecision], None] | None = None,
    ) -> None:
        self._restart_policy = restart_policy or RestartPolicy()
        self._mailbox_drain_policy = mailbox_drain_policy or MailboxDrainPolicy()
        self._ask_context_policy = ask_context_policy or AskContextPolicy()
        self._registered: dict[ActorPath, ActorRef] = {}
        self._failed_paths: set[ActorPath] = set()
        self._failure_events: list[ActorFailureEvent] = []
        self._failure_times: dict[str, list[datetime]] = {}
        self._on_failure = on_failure
        self._on_decision = on_decision

    @property
    def restart_policy(self) -> RestartPolicy:
        """Return the configured restart policy."""
        return self._restart_policy

    @property
    def mailbox_drain_policy(self) -> MailboxDrainPolicy:
        """Return the configured mailbox drain policy."""
        return self._mailbox_drain_policy

    @property
    def ask_context_policy(self) -> AskContextPolicy:
        """Return the configured ask-context policy."""
        return self._ask_context_policy

    def supervise(self, actor_ref: ActorRef, *, path: ActorPath) -> None:
        """Register an actor for supervision.

        The supervisor stores a mapping from path to ActorRef so that restart
        policy can re-wire and drain the actor's mailbox.  The ActorRef should
        also have this supervisor (or a callback wrapping it) set as its
        ``failure_sink``.
        """
        self._registered[path] = actor_ref

    def handle_failure(self, event: ActorFailureEvent) -> SupervisorDecision:
        """Decide what to do on actor failure and return the decision.

        Records the failure, applies the restart policy against the actor's
        prior failure history within the policy window, and returns
        :attr:`SupervisorDecision.RESTART` or :attr:`SupervisorDecision.DEGRADE`.
        On ``RESTART`` the failed actor's mailbox is handled per the configured
        :class:`~qts.runtime.actor_policies.MailboxDrainPolicy`.
        """
        prior_failures = tuple(self._failure_times.get(event.actor_name, ()))
        now = event.timestamp if event.timestamp is not None else datetime.now(tz=UTC)
        self._failure_events.append(event)
        self._failure_times.setdefault(event.actor_name, []).append(now)

        matching_path = self._find_path_by_name(event.actor_name)
        if matching_path is not None:
            self._failed_paths.add(matching_path)

        should_restart = self._restart_policy.should_restart(
            prior_failures,
            now=now,
            recoverable=event.recoverable,
        )
        decision = SupervisorDecision.RESTART if should_restart else SupervisorDecision.DEGRADE

        if decision is SupervisorDecision.RESTART:
            logger.warning(
                "actor failure (restarting): %s %s: %s",
                event.actor_name,
                event.exception_type,
                event.exception_message,
            )
            if matching_path is not None:
                self._restart(matching_path)
        else:
            logger.error(
                "actor failure (degrading): %s %s: %s (recoverable=%s, prior=%d)",
                event.actor_name,
                event.exception_type,
                event.exception_message,
                event.recoverable,
                len(prior_failures),
            )

        if self._on_failure is not None:
            self._on_failure(event)
        if self._on_decision is not None:
            self._on_decision(event, decision)
        return decision

    def _restart(self, path: ActorPath) -> tuple[object, ...]:
        """Apply the mailbox drain policy to a restarting actor.

        Returns the drained messages (empty when the policy preserves the
        mailbox).  The path remains recorded in ``failed_paths`` because it has
        experienced a failure; the restart only governs mailbox handling.
        """
        actor_ref = self._registered.get(path)
        if actor_ref is None:
            return ()
        return self._mailbox_drain_policy.apply(actor_ref.mailbox)

    @property
    def failure_events(self) -> tuple[ActorFailureEvent, ...]:
        """Return all recorded failure events."""
        return tuple(self._failure_events)

    @property
    def failed_paths(self) -> frozenset[ActorPath]:
        """Return paths of actors that have experienced a failure."""
        return frozenset(self._failed_paths)

    def is_failed(self, path: ActorPath) -> bool:
        """Check whether a supervised actor has experienced a failure."""
        return path in self._failed_paths

    def failure_count(self, actor_name: str) -> int:
        """Return the total number of failures recorded for *actor_name*."""
        return len(self._failure_times.get(actor_name, ()))

    def _find_path_by_name(self, actor_name: str) -> ActorPath | None:
        """Find a registered path matching the actor name string."""
        for path in self._registered:
            if str(path) == actor_name:
                return path
        return None


class RuntimeSupervisionCoordinator:
    """Bridge actor failures to runtime-session lifecycle transitions.

    This is the production caller for :class:`ActorSupervisor`.  It owns a
    supervisor whose decisions are mapped onto the ``RuntimeSession`` facade:
    a :attr:`SupervisorDecision.RESTART` lets the session continue (the actor
    is restarted in place per the supervisor's mailbox policy), while a
    :attr:`SupervisorDecision.DEGRADE`/:attr:`SupervisorDecision.ESCALATE`
    transitions a running/paused session to ``DEGRADED`` so it stops accepting
    new work while observability stays alive.

    The coordinator depends on ``_RuntimeSupervisionSessionPort`` instead of
    reaching through ``RuntimeSession`` private attributes; ``RuntimeSession``
    owns the explicit port methods.
    """

    def __init__(
        self,
        session: _RuntimeSupervisionSessionPort,
        *,
        supervisor: ActorSupervisor | None = None,
    ) -> None:
        self._session = session
        self._supervisor = supervisor or ActorSupervisor()
        self._register_session_actors()

    @property
    def supervisor(self) -> ActorSupervisor:
        """Return the owned supervisor."""
        return self._supervisor

    def supervise(self, actor_ref: ActorRef, *, path: ActorPath) -> None:
        """Register a supervised actor with the owned supervisor."""
        self._supervisor.supervise(actor_ref, path=path)

    def _register_session_actors(self) -> None:
        """Register the session's per-account partition actors for supervision.

        Registration lets the restart policy drain a failed actor's mailbox via
        the configured :class:`~qts.runtime.actor_policies.MailboxDrainPolicy`.
        Each partition contributes its account, order-manager, and execution
        actors under a stable ``/<account>/<role>`` path.
        """
        for account_id, partition in self._session.supervised_actor_partitions():
            account_segment = account_id.value if account_id is not None else "default"
            root = ActorPath.root(account_segment)
            self._supervisor.supervise(partition.account_ref, path=root.child("account"))
            self._supervisor.supervise(
                partition.order_manager_ref, path=root.child("order_manager")
            )
            self._supervisor.supervise(partition.execution_ref, path=root.child("execution"))

    def on_actor_failure(self, event: ActorFailureEvent) -> SupervisorDecision:
        """Apply the supervisor decision for *event* to the runtime session.

        Returns the :class:`SupervisorDecision` taken so callers and tests can
        assert on it.  Emitting the :class:`ActorFailureEvent` is the
        supervisor's responsibility; this method additionally records a runtime
        event and degrades the session when the decision is not a restart.
        """
        from qts.runtime.state import RuntimeSessionState

        decision = self._supervisor.handle_failure(event)
        session = self._session
        session.write_supervisor_event(
            "runtime.actor_failure",
            {
                "actor_name": event.actor_name,
                "exception_type": event.exception_type,
                "exception_message": event.exception_message,
                "recoverable": event.recoverable,
                "decision": decision.name,
                "failure_count": self._supervisor.failure_count(event.actor_name),
            },
        )
        if decision is not SupervisorDecision.RESTART and session.state in {
            RuntimeSessionState.RUNNING,
            RuntimeSessionState.PAUSED,
        }:
            session.degrade()
        return decision


__all__ = [
    "ActorSupervisor",
    "RuntimeSupervisionCoordinator",
    "SupervisorDecision",
]
