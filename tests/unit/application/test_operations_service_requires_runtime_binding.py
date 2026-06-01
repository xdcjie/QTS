"""OperationsService safety/lifecycle commands require a bound runtime.

QTS-FINAL-001: with no RuntimeSession bound, lifecycle (start/stop/pause/resume)
and kill-switch activation must raise ``RuntimeCommandNotBound`` rather than
mutate shadow state and report success. With a runtime bound through
``RuntimeCommandExecutor`` the same commands act on the real session.
"""

from __future__ import annotations

from qts.application.dto import KillSwitchCommandDTO
from qts.application.services import OperationsService

from tests.support.operations import FakeControlPlaneSession, bound_operations_service


def test_unbound_service_returns_rejected_results_for_operator_commands() -> None:
    service = OperationsService()  # no command_executor bound

    results = [
        service.start_runtime_result(operator_id="ops-a", runtime_instance_id="rt-unbound"),
        service.stop_runtime_result(operator_id="ops-a", runtime_instance_id="rt-unbound"),
        service.pause_runtime_result(operator_id="ops-a", runtime_instance_id="rt-unbound"),
        service.activate_kill_switch_result(
            KillSwitchCommandDTO(scope="global", reason="halt"),
            operator_id="ops-a",
            runtime_instance_id="rt-unbound",
        ),
    ]

    assert {result.status for result in results} == {"rejected"}
    assert {result.reason_code for result in results} == {"RUNTIME_SESSION_NOT_BOUND"}


def test_bound_service_acts_on_the_runtime_session() -> None:
    session = FakeControlPlaneSession()
    service = bound_operations_service(session)

    paused = service.pause_runtime(
        runtime_instance_id="rt-test", operator_id="ops-a", idempotency_key="p1"
    )
    halt = service.activate_kill_switch(
        KillSwitchCommandDTO(scope="global", reason="halt"),
        operator_id="ops-a",
        runtime_instance_id="rt-test",
        idempotency_key="k1",
    )

    assert paused.state == "paused"
    assert halt.active is True
    # The commands reached the bound runtime session.
    assert "pause" in session.calls
    assert "activate_kill_switch" in session.calls
