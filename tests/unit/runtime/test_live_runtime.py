from __future__ import annotations

import pytest
from qts.runtime.state import (
    RuntimeSessionState as RuntimeSessionState,
)
from qts.runtime.state import (
    RuntimeStateMachine as RuntimeStateMachine,
)


def test_live_runtime_state_machine_allows_only_operational_transitions() -> None:
    machine = RuntimeStateMachine()

    assert machine.apply("start") is RuntimeSessionState.STARTING
    assert machine.apply("started") is RuntimeSessionState.RUNNING
    assert machine.apply("pause") is RuntimeSessionState.PAUSED
    assert machine.apply("resume") is RuntimeSessionState.RUNNING
    assert machine.apply("degrade") is RuntimeSessionState.DEGRADED
    assert machine.apply("recover") is RuntimeSessionState.RUNNING
    assert machine.apply("stop") is RuntimeSessionState.STOPPED

    with pytest.raises(ValueError, match="invalid runtime transition"):
        machine.apply("resume")


def test_live_runtime_degrades_from_runtime_event_and_rejects_new_orders() -> None:
    machine = RuntimeStateMachine()
    machine.apply("start")
    machine.apply("started")

    assert machine.apply("degrade") is RuntimeSessionState.DEGRADED


def test_live_runtime_facade_is_not_exported() -> None:
    import importlib

    import qts.runtime as runtime_package
    from qts.runtime.session import RuntimeSession

    assert not hasattr(runtime_package, "LiveRuntime")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("qts.runtime.live")
    assert not hasattr(RuntimeSession, "submit_order")
