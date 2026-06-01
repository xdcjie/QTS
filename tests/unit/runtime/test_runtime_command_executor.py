"""RuntimeCommandExecutor executes against a bound session or fails loudly.

QTS-FINAL-001: operator commands must act on a real RuntimeSession or raise
``RuntimeCommandNotBound`` (surfaced as ``RUNTIME_SESSION_NOT_BOUND``) — never a
silent no-op. These tests lock the registry resolution and the bound/unbound
executor behaviour without standing up a full actor-backed session.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from qts.runtime.control_plane import (
    RuntimeCommandExecutor,
    RuntimeSessionKey,
    RuntimeSessionRegistry,
)
from qts.runtime.errors import RuntimeCommandNotBound
from qts.runtime.session import RuntimeSession


class _RecordingSession:
    """Minimal stand-in recording the lifecycle/kill-switch calls it receives."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.account_snapshot = "snapshot-sentinel"

    def start(self) -> str:
        self.calls.append("start")
        return "STARTED"

    def stop(self) -> str:
        self.calls.append("stop")
        return "STOPPED"

    def pause(self) -> str:
        self.calls.append("pause")
        return "PAUSED"

    def resume(self) -> str:
        self.calls.append("resume")
        return "RESUMED"

    def recover(self) -> str:
        self.calls.append("recover")
        return "RECOVERED"

    def enter_observation(self) -> str:
        self.calls.append("enter_observation")
        return "OBSERVATION"

    def exit_observation(self) -> str:
        self.calls.append("exit_observation")
        return "RESUMED"

    def activate_kill_switch(self, command: Any) -> str:
        self.calls.append("activate_kill_switch")
        return f"evidence:{command}"

    def deactivate_kill_switch(self, command: Any) -> str:
        self.calls.append("deactivate_kill_switch")
        return f"deactivated:{command}"


def _executor_with_session() -> tuple[RuntimeCommandExecutor, _RecordingSession, RuntimeSessionKey]:
    registry = RuntimeSessionRegistry()
    session = _RecordingSession()
    key = RuntimeSessionKey(runtime_instance_id="rt-1", environment="paper")
    registry.register(key, cast(RuntimeSession, session))
    return RuntimeCommandExecutor(registry), session, key


def test_unbound_executor_raises_runtime_command_not_bound() -> None:
    executor = RuntimeCommandExecutor(RuntimeSessionRegistry())
    command = pytest.importorskip("qts.risk.kill_switch").RuntimeKillSwitchCommand(
        operator_id="ops", reason="halt"
    )

    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.start()
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.stop()
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.pause()
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.snapshot()
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.activate_kill_switch(command)
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.deactivate_kill_switch(command)
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.enter_observation()
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        executor.exit_observation()


def test_bound_executor_delegates_lifecycle_to_the_session() -> None:
    executor, session, _ = _executor_with_session()

    assert executor.start() == "STARTED"
    assert executor.stop() == "STOPPED"
    assert executor.pause() == "PAUSED"
    assert executor.resume() == "RESUMED"
    assert executor.reconcile() == "RECOVERED"
    assert executor.enter_observation() == "OBSERVATION"
    assert executor.exit_observation() == "RESUMED"
    assert cast(object, executor.snapshot()) == "snapshot-sentinel"
    assert session.calls == [
        "start",
        "stop",
        "pause",
        "resume",
        "recover",
        "enter_observation",
        "exit_observation",
    ]


def test_bound_executor_routes_kill_switch_to_the_session() -> None:
    executor, session, _ = _executor_with_session()
    command = pytest.importorskip("qts.risk.kill_switch").RuntimeKillSwitchCommand(
        operator_id="ops", reason="halt"
    )

    evidence = executor.activate_kill_switch(command)
    deactivated = executor.deactivate_kill_switch(command)

    assert "activate_kill_switch" in session.calls
    assert "deactivate_kill_switch" in session.calls
    assert str(evidence).startswith("evidence:")
    assert str(deactivated).startswith("deactivated:")


def test_registry_resolves_by_key_and_primary_only_when_single() -> None:
    registry = RuntimeSessionRegistry()
    assert registry.is_empty()
    assert registry.primary() is None

    key_a = RuntimeSessionKey(runtime_instance_id="rt-a")
    key_b = RuntimeSessionKey(runtime_instance_id="rt-b")
    session_a = cast(RuntimeSession, _RecordingSession())
    session_b = cast(RuntimeSession, _RecordingSession())
    registry.register(key_a, session_a)
    assert registry.resolve(key_a) is session_a
    assert registry.primary() is session_a  # exactly one bound

    registry.register(key_b, session_b)
    assert registry.primary() is None  # ambiguous with two bound
    assert registry.resolve(key_b) is session_b

    registry.unregister(key_a)
    assert registry.resolve(key_a) is None
    assert registry.primary() is session_b


def test_session_key_rejects_empty_instance_id() -> None:
    with pytest.raises(ValueError, match="runtime_instance_id must not be empty"):
        RuntimeSessionKey(runtime_instance_id="  ")
