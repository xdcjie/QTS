"""Operator commands target the registered runtime_instance_id."""

from __future__ import annotations

from typing import cast

from qts.application.services.operations import OperationsService
from qts.runtime.control_plane import (
    RuntimeCommandExecutor,
    RuntimeSessionKey,
    RuntimeSessionRegistry,
)
from qts.runtime.session import RuntimeSession
from qts.runtime.state import RuntimeSessionState


class _FakeRuntimeSession:
    def __init__(self) -> None:
        self.pause_count = 0
        self.state = RuntimeSessionState.RUNNING

    def pause(self) -> RuntimeSessionState:
        self.pause_count += 1
        self.state = RuntimeSessionState.PAUSED
        return self.state


def test_operator_command_targets_registered_runtime_instance_id() -> None:
    registry = RuntimeSessionRegistry()
    rt_a = _FakeRuntimeSession()
    rt_b = _FakeRuntimeSession()
    registry.register(RuntimeSessionKey(runtime_instance_id="rt-a"), cast(RuntimeSession, rt_a))
    registry.register(RuntimeSessionKey(runtime_instance_id="rt-b"), cast(RuntimeSession, rt_b))
    operations = OperationsService(command_executor=RuntimeCommandExecutor(registry))

    result = operations.pause_runtime_result(
        runtime_instance_id="rt-b",
        operator_id="ops",
        idempotency_key="pause-rt-b",
    )

    assert result.status == "completed"
    assert result.evidence["runtime_instance_id"] == "rt-b"
    assert rt_a.pause_count == 0
    assert rt_b.pause_count == 1
