"""Broker connectivity lifecycle coordination for runtime sessions."""

from __future__ import annotations

from typing import Any, cast

from qts.runtime.state import RuntimeSessionState


class RuntimeBrokerLifecycleCoordinator:
    """Own broker disconnect/reconnect state transitions and audit events."""

    def __init__(self, session: Any) -> None:
        self._session = session

    def on_broker_disconnect(self, *, reason: str) -> RuntimeSessionState:
        """Mark the session degraded after broker connectivity is lost."""
        if not reason.strip():
            raise ValueError("reason must not be empty")
        session = self._session
        session._write_event(
            "runtime.broker_disconnected",
            {"reason": reason, "state_before": session.state.value},
        )
        if session.state in {RuntimeSessionState.RUNNING, RuntimeSessionState.PAUSED}:
            return cast(RuntimeSessionState, session.degrade())
        return cast(RuntimeSessionState, session.state)

    def on_broker_reconnect(
        self,
        *,
        reason: str,
        reconciliation_passed: bool,
    ) -> RuntimeSessionState:
        """Recover from broker reconnect only after reconciliation passes."""
        if not reason.strip():
            raise ValueError("reason must not be empty")
        session = self._session
        session._write_event(
            "runtime.broker_reconnected",
            {
                "reason": reason,
                "reconciliation_passed": reconciliation_passed,
                "state_before": session.state.value,
            },
        )
        if reconciliation_passed:
            if session.state is RuntimeSessionState.DEGRADED:
                return cast(RuntimeSessionState, session.recover())
            return cast(RuntimeSessionState, session.state)
        if session.state in {RuntimeSessionState.RUNNING, RuntimeSessionState.PAUSED}:
            return cast(RuntimeSessionState, session.degrade())
        return cast(RuntimeSessionState, session.state)


__all__ = ["RuntimeBrokerLifecycleCoordinator"]
