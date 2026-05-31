"""OperationsService safety/lifecycle commands require a bound runtime.

QTS-FINAL-001: with no RuntimeSession bound, lifecycle (start/stop/pause/resume)
and kill-switch activation must raise ``RuntimeCommandNotBound`` rather than
mutate shadow state and report success. With a runtime bound through
``RuntimeCommandExecutor`` the same commands act on the real session.
"""

from __future__ import annotations

import pytest
from qts.application.dto import KillSwitchCommandDTO
from qts.application.services import OperationsService
from qts.runtime.errors import RuntimeCommandNotBound

from tests.support.operations import FakeControlPlaneSession, bound_operations_service


def test_unbound_service_raises_on_lifecycle_and_kill_switch() -> None:
    service = OperationsService()  # no command_executor bound

    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        service.start_runtime(operator_id="ops-a")
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        service.stop_runtime(operator_id="ops-a")
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        service.pause_runtime(operator_id="ops-a")
    with pytest.raises(RuntimeCommandNotBound, match="RUNTIME_SESSION_NOT_BOUND"):
        service.activate_kill_switch(
            KillSwitchCommandDTO(scope="global", reason="halt"),
            operator_id="ops-a",
        )


def test_bound_service_acts_on_the_runtime_session() -> None:
    session = FakeControlPlaneSession()
    service = bound_operations_service(session)

    paused = service.pause_runtime(operator_id="ops-a", idempotency_key="p1")
    halt = service.activate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="halt"),
        operator_id="ops-a",
        idempotency_key="k1",
    )

    assert paused.state == "paused"
    assert halt.active is True
    # The commands reached the bound runtime session.
    assert "pause" in session.calls
    assert "activate_kill_switch" in session.calls
