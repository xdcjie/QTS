"""QTS-FINAL-012: RuntimeSafetyController depends on the narrow safety port.

The controller mutates kill-switch state and writes evidence through
``RuntimeSafetySessionPort`` / ``RuntimeSafetyState``, and never reaches into
``RuntimeSession`` private attributes.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping

import pytest
from qts.runtime.broker_runtime_topology import AccountRuntimePartition
from qts.runtime.mode import RuntimeMode
from qts.runtime.safety import RuntimeKillSwitchDeactivateCommand
from qts.runtime.safety_controller import RuntimeSafetyController
from qts.runtime.safety_port import RuntimeSafetySessionPort, RuntimeSafetyState
from qts.runtime.state import RuntimeSessionState


class _RecordingPort:
    """Recording RuntimeSafetySessionPort for deactivate/blocked-reason tests."""

    def __init__(self) -> None:
        self._safety_state = RuntimeSafetyState(kill_switch_active=True)
        self.events: list[tuple[str, dict[str, object]]] = []

    @property
    def safety_state(self) -> RuntimeSafetyState:
        return self._safety_state

    @property
    def runtime_state(self) -> RuntimeSessionState:
        return RuntimeSessionState.RUNNING

    @property
    def mode(self) -> RuntimeMode:
        return RuntimeMode.PAPER_SIMULATED

    @property
    def startup_decision(self) -> object:
        return None

    @property
    def run_id(self) -> str:
        return "test-run"

    @property
    def primary_partition(self) -> AccountRuntimePartition:
        raise NotImplementedError

    def account_partitions(self) -> tuple[AccountRuntimePartition, ...]:
        raise NotImplementedError

    def active_order_ids(self) -> tuple[str, ...]:
        return ()

    def record_account_snapshots(self) -> tuple[str, ...]:
        return ()

    def write_event(self, kind: str, payload: Mapping[str, object]) -> None:
        self.events.append((kind, dict(payload)))


def test_recording_port_satisfies_the_protocol() -> None:
    assert isinstance(_RecordingPort(), RuntimeSafetySessionPort)


def test_controller_deactivate_goes_through_port_state_and_events() -> None:
    port = _RecordingPort()
    controller = RuntimeSafetyController(port)

    controller.deactivate_kill_switch(
        RuntimeKillSwitchDeactivateCommand(operator_id="ops-a", reason="resume", authorized=True)
    )

    assert port.safety_state.kill_switch_active is False
    assert [kind for kind, _ in port.events] == ["runtime.kill_switch_deactivated"]


def test_controller_unauthorized_deactivate_does_not_touch_state() -> None:
    port = _RecordingPort()
    controller = RuntimeSafetyController(port)

    with pytest.raises(PermissionError):
        controller.deactivate_kill_switch(
            RuntimeKillSwitchDeactivateCommand(
                operator_id="ops-a", reason="resume", authorized=False
            )
        )

    # State unchanged and no event written when authorization is missing.
    assert port.safety_state.kill_switch_active is True
    assert port.events == []


def test_controller_source_does_not_reference_session_privates() -> None:
    source = inspect.getsource(RuntimeSafetyController)
    assert "_session" not in source
    assert "_kill_switch_active" not in source
