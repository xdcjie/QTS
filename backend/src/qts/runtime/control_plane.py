"""Operator control-plane binding for live RuntimeSessions.

Operator commands (start/stop/pause/resume/reconcile/snapshot/kill-switch) must
act on a *real* running ``RuntimeSession`` or fail loudly — never mutate a shadow
application-local state and report success (QTS-FINAL-001). ``RuntimeSessionRegistry``
holds the bound sessions keyed by their identity, and ``RuntimeCommandExecutor``
executes commands against the resolved session, raising ``RuntimeCommandNotBound``
when no runtime is bound so the API can return ``RUNTIME_SESSION_NOT_BOUND`` rather
than a safety-critical no-op.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qts.runtime.errors import RuntimeCommandNotBound

if TYPE_CHECKING:
    from qts.risk.kill_switch import RuntimeKillSwitchCommand
    from qts.runtime.actors.account_actor import AccountSnapshot
    from qts.runtime.safety import RuntimeKillSwitchEvidence
    from qts.runtime.session import RuntimeSession
    from qts.runtime.state import RuntimeSessionState


@dataclass(frozen=True, slots=True)
class RuntimeSessionKey:
    """Identity a bound RuntimeSession is registered under."""

    runtime_instance_id: str
    run_id: str | None = None
    account_id: str | None = None
    environment: str | None = None

    def __post_init__(self) -> None:
        """Validate that the runtime instance identifier is non-empty."""
        if not self.runtime_instance_id.strip():
            raise ValueError("runtime_instance_id must not be empty")


class RuntimeSessionRegistry:
    """Hold the live RuntimeSessions an operator control plane can act on."""

    def __init__(self) -> None:
        """Create an empty registry of bound runtime sessions."""
        self._sessions: dict[RuntimeSessionKey, RuntimeSession] = {}

    def register(self, key: RuntimeSessionKey, session: RuntimeSession) -> None:
        """Bind ``session`` under ``key``, replacing any existing binding."""
        self._sessions[key] = session

    def unregister(self, key: RuntimeSessionKey) -> None:
        """Remove the binding for ``key`` if present."""
        self._sessions.pop(key, None)

    def resolve(self, key: RuntimeSessionKey) -> RuntimeSession | None:
        """Return the session bound under ``key``, or ``None`` if unbound."""
        return self._sessions.get(key)

    def primary(self) -> RuntimeSession | None:
        """Return the only bound session, or ``None`` unless exactly one is bound."""
        if len(self._sessions) != 1:
            return None
        return next(iter(self._sessions.values()))

    def is_empty(self) -> bool:
        """Return whether no runtime session is currently bound."""
        return not self._sessions


class RuntimeCommandExecutor:
    """Execute operator commands against a bound RuntimeSession or fail loudly."""

    def __init__(self, registry: RuntimeSessionRegistry) -> None:
        """Create an executor backed by ``registry`` of bound sessions."""
        self._registry = registry

    def _require_session(self, key: RuntimeSessionKey | None) -> RuntimeSession:
        session = self._registry.resolve(key) if key is not None else self._registry.primary()
        if session is None:
            raise RuntimeCommandNotBound(
                "RUNTIME_SESSION_NOT_BOUND: no RuntimeSession is bound to handle this command"
            )
        return session

    def start(self, *, key: RuntimeSessionKey | None = None) -> RuntimeSessionState:
        """Start the bound runtime session."""
        return self._require_session(key).start()

    def stop(self, *, key: RuntimeSessionKey | None = None) -> RuntimeSessionState:
        """Stop the bound runtime session."""
        return self._require_session(key).stop()

    def pause(self, *, key: RuntimeSessionKey | None = None) -> RuntimeSessionState:
        """Pause new strategy intent processing on the bound runtime session."""
        return self._require_session(key).pause()

    def resume(self, *, key: RuntimeSessionKey | None = None) -> RuntimeSessionState:
        """Resume strategy intent processing on the bound runtime session."""
        return self._require_session(key).resume()

    def reconcile(self, *, key: RuntimeSessionKey | None = None) -> RuntimeSessionState:
        """Recover (reconcile) the bound runtime session after degradation."""
        return self._require_session(key).recover()

    def snapshot(self, *, key: RuntimeSessionKey | None = None) -> AccountSnapshot:
        """Return the current account snapshot from the bound runtime session."""
        return self._require_session(key).account_snapshot

    def activate_kill_switch(
        self,
        command: RuntimeKillSwitchCommand,
        *,
        key: RuntimeSessionKey | None = None,
    ) -> RuntimeKillSwitchEvidence:
        """Activate the kill switch on the bound runtime session and return its evidence."""
        return self._require_session(key).activate_kill_switch(command)


__all__ = [
    "RuntimeCommandExecutor",
    "RuntimeSessionKey",
    "RuntimeSessionRegistry",
]
