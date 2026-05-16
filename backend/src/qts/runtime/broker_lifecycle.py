"""Broker connectivity lifecycle coordination for runtime sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, cast

from qts.runtime.state import RuntimeSessionState


@dataclass(frozen=True, slots=True)
class BrokerReconnectReconciliationResult:
    """Reconciliation outcome for broker reconnect recovery."""

    passed: bool
    reason_code: str | None = None
    drift_count: int = 0
    unresolved_callback_count: int = 0

    def __post_init__(self) -> None:
        if self.passed and self.reason_code is not None:
            raise ValueError("passed reconnect reconciliation must not have a reason_code")
        if not self.passed and not self.reason_code:
            raise ValueError("failed reconnect reconciliation requires a reason_code")
        if self.drift_count < 0:
            raise ValueError("drift_count must be non-negative")
        if self.unresolved_callback_count < 0:
            raise ValueError("unresolved_callback_count must be non-negative")


class BrokerReconnectReconciliation(Protocol):
    """Broker refresh boundary required before reconnect recovery."""

    def resubscribe_market_data(self) -> None:
        """Restore active market-data subscriptions before reconciliation."""
        ...

    def refresh_open_orders(self) -> None:
        """Request broker open orders before reconciliation."""
        ...

    def refresh_positions(self) -> None:
        """Request broker positions before reconciliation."""
        ...

    def refresh_executions(self) -> None:
        """Request broker executions before reconciliation."""
        ...

    def refresh_account_summary(self) -> None:
        """Request broker account summary before reconciliation."""
        ...

    def reconcile_after_reconnect(self) -> BrokerReconnectReconciliationResult:
        """Reconcile refreshed broker state against runtime state."""
        ...


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
    ) -> RuntimeSessionState:
        """Recover from broker reconnect only after reconciliation passes."""
        if not reason.strip():
            raise ValueError("reason must not be empty")
        session = self._session
        state_before = session.state
        session._write_event(
            "runtime.broker_reconnected",
            {
                "reason": reason,
                "state_before": state_before.value,
            },
        )

        reconciliation = session._dependencies.broker_reconnect_reconciliation
        if reconciliation is None:
            session._write_event(
                "runtime.reconciliation_failed",
                {
                    "reason_code": "RECONNECT_RECONCILIATION_NOT_CONFIGURED",
                    "state_before": session.state.value,
                },
            )
            if session.state in {RuntimeSessionState.RUNNING, RuntimeSessionState.PAUSED}:
                return cast(RuntimeSessionState, session.degrade())
            return cast(RuntimeSessionState, session.state)

        reconciliation.resubscribe_market_data()
        reconciliation.refresh_open_orders()
        reconciliation.refresh_positions()
        reconciliation.refresh_executions()
        reconciliation.refresh_account_summary()
        result = reconciliation.reconcile_after_reconnect()

        if result.passed:
            session._write_event(
                "runtime.reconciliation_passed",
                {
                    "reason": reason,
                    "state_before": session.state.value,
                    "drift_count": result.drift_count,
                    "unresolved_callback_count": result.unresolved_callback_count,
                },
            )
            if session.state is RuntimeSessionState.DEGRADED:
                return cast(RuntimeSessionState, session.recover())
            return cast(RuntimeSessionState, session.state)

        session._write_event(
            "runtime.reconciliation_failed",
            {
                "reason_code": result.reason_code,
                "state_before": session.state.value,
                "drift_count": result.drift_count,
                "unresolved_callback_count": result.unresolved_callback_count,
            },
        )
        if session.state in {RuntimeSessionState.RUNNING, RuntimeSessionState.PAUSED}:
            return cast(RuntimeSessionState, session.degrade())
        return cast(RuntimeSessionState, session.state)


__all__ = [
    "BrokerReconnectReconciliation",
    "BrokerReconnectReconciliationResult",
    "RuntimeBrokerLifecycleCoordinator",
]
