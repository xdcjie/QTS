from __future__ import annotations

import pytest
from qts.runtime.live import LiveRuntimeState, LiveRuntimeStateMachine


def test_live_runtime_state_machine_allows_only_operational_transitions() -> None:
    machine = LiveRuntimeStateMachine()

    assert machine.apply("start") is LiveRuntimeState.STARTING
    assert machine.apply("started") is LiveRuntimeState.RUNNING
    assert machine.apply("pause") is LiveRuntimeState.PAUSED
    assert machine.apply("resume") is LiveRuntimeState.RUNNING
    assert machine.apply("degrade") is LiveRuntimeState.DEGRADED
    assert machine.apply("recover") is LiveRuntimeState.RUNNING
    assert machine.apply("stop") is LiveRuntimeState.STOPPED

    with pytest.raises(ValueError, match="invalid live runtime transition"):
        machine.apply("resume")
