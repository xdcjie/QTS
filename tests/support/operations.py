"""Test support for operator control-plane wiring (QTS-FINAL-001).

Provides a lightweight ``RuntimeSession`` stand-in bound through the real
``RuntimeCommandExecutor`` / ``RuntimeSessionRegistry`` so application and API
tests can exercise the control plane against a "bound" runtime without standing
up a full actor topology. Behavioural / order-blocking guarantees are covered by
the integration tests that use a real ``RuntimeSession``; this helper only proves
the command-routing + binding contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from qts.application.services import OperationsService
from qts.runtime.control_plane import (
    RuntimeCommandExecutor,
    RuntimeSessionKey,
    RuntimeSessionRegistry,
)
from qts.runtime.session import RuntimeSession
from qts.runtime.state import RuntimeSessionState


@dataclass(slots=True)
class _FakeKillSwitchEvidence:
    """Minimal kill-switch evidence the control-plane handler reads back."""

    runtime_state: str = "stopped"
    active_order_ids: tuple[str, ...] = ()
    cancelled_order_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class FakeControlPlaneSession:
    """RuntimeSession stand-in recording operator lifecycle/kill-switch calls."""

    state_value: RuntimeSessionState = RuntimeSessionState.RUNNING
    calls: list[str] = field(default_factory=list)

    def start(self) -> RuntimeSessionState:
        self.calls.append("start")
        self.state_value = RuntimeSessionState.RUNNING
        return self.state_value

    def stop(self) -> RuntimeSessionState:
        self.calls.append("stop")
        self.state_value = RuntimeSessionState.STOPPED
        return self.state_value

    def pause(self) -> RuntimeSessionState:
        self.calls.append("pause")
        self.state_value = RuntimeSessionState.PAUSED
        return self.state_value

    def resume(self) -> RuntimeSessionState:
        self.calls.append("resume")
        self.state_value = RuntimeSessionState.RUNNING
        return self.state_value

    def enter_observation(self) -> RuntimeSessionState:
        self.calls.append("enter_observation")
        self.state_value = RuntimeSessionState.OBSERVATION
        return self.state_value

    def exit_observation(self) -> RuntimeSessionState:
        self.calls.append("exit_observation")
        self.state_value = RuntimeSessionState.RUNNING
        return self.state_value

    def recover(self) -> RuntimeSessionState:
        self.calls.append("recover")
        self.state_value = RuntimeSessionState.RUNNING
        return self.state_value

    @property
    def account_snapshot(self) -> object:
        return {"cash": {}}

    def activate_kill_switch(self, command: object) -> _FakeKillSwitchEvidence:
        self.calls.append("activate_kill_switch")
        self.state_value = RuntimeSessionState.STOPPED
        return _FakeKillSwitchEvidence(runtime_state=self.state_value.value)

    def deactivate_kill_switch(self, command: object) -> RuntimeSessionState:
        self.calls.append("deactivate_kill_switch")
        return self.state_value


def bound_command_executor(
    session: FakeControlPlaneSession | None = None,
    runtime_instance_id: str = "rt-test",
) -> tuple[RuntimeCommandExecutor, FakeControlPlaneSession, str]:
    """Return an executor bound to a fake control-plane session."""
    bound_session = session or FakeControlPlaneSession()
    registry = RuntimeSessionRegistry()
    registry.register(
        RuntimeSessionKey(runtime_instance_id=runtime_instance_id),
        cast(RuntimeSession, bound_session),
    )
    return RuntimeCommandExecutor(registry), bound_session, runtime_instance_id


def bound_operations_service(
    session: FakeControlPlaneSession | None = None,
    runtime_instance_id: str = "rt-test",
) -> OperationsService:
    """Return an OperationsService whose commands act on a bound fake session."""
    executor, _, _ = bound_command_executor(
        session=session,
        runtime_instance_id=runtime_instance_id,
    )
    return OperationsService(command_executor=executor)


DEFAULT_RUNTIME_INSTANCE_ID = "rt-test"


__all__ = [
    "DEFAULT_RUNTIME_INSTANCE_ID",
    "FakeControlPlaneSession",
    "bound_command_executor",
    "bound_operations_service",
]
