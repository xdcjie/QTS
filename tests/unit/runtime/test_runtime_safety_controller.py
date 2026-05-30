from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from qts.runtime.broker_runtime_topology import AccountRuntimePartition
from qts.runtime.mode import RuntimeMode
from qts.runtime.safety_port import RuntimeSafetyState
from qts.runtime.state import RuntimeSessionState


@dataclass(slots=True)
class _OrderPermission:
    allows_order_submission: bool
    allows_live_orders: bool = False


@dataclass(slots=True)
class _StartupDecision:
    order_permission: _OrderPermission
    real_order_submission_enabled: bool = False


class _FakeSafetyPort:
    """Minimal RuntimeSafetySessionPort for blocked_reason gate tests."""

    def __init__(
        self,
        *,
        runtime_state: RuntimeSessionState,
        mode: RuntimeMode = RuntimeMode.PAPER_SIMULATED,
        startup_decision: _StartupDecision | None = None,
    ) -> None:
        self._safety_state = RuntimeSafetyState()
        self._runtime_state = runtime_state
        self._mode = mode
        self._startup_decision = startup_decision

    @property
    def safety_state(self) -> RuntimeSafetyState:
        return self._safety_state

    @property
    def runtime_state(self) -> RuntimeSessionState:
        return self._runtime_state

    @runtime_state.setter
    def runtime_state(self, value: RuntimeSessionState) -> None:
        self._runtime_state = value

    @property
    def mode(self) -> RuntimeMode:
        return self._mode

    @property
    def startup_decision(self) -> object:
        return self._startup_decision

    @property
    def run_id(self) -> str:
        return "test-run"

    @property
    def primary_partition(self) -> AccountRuntimePartition:
        raise NotImplementedError("blocked_reason tests do not touch partitions")

    def account_partitions(self) -> tuple[AccountRuntimePartition, ...]:
        raise NotImplementedError("blocked_reason tests do not touch partitions")

    def active_order_ids(self) -> tuple[str, ...]:
        return ()

    def record_account_snapshots(self) -> tuple[str, ...]:
        return ()

    def write_event(self, kind: str, payload: Mapping[str, object]) -> None:
        return None


def test_runtime_safety_controller_blocks_with_existing_reason_codes() -> None:
    from qts.runtime.safety_controller import RuntimeSafetyController

    port = _FakeSafetyPort(runtime_state=RuntimeSessionState.RUNNING)
    controller = RuntimeSafetyController(port)

    port.safety_state.activate_kill_switch()
    assert controller.blocked_reason() == "KILL_SWITCH_ACTIVE"

    port.safety_state.deactivate_kill_switch()
    port.runtime_state = RuntimeSessionState.PAUSED
    assert controller.blocked_reason() == "RUNTIME_PAUSED"

    port.runtime_state = RuntimeSessionState.DEGRADED
    assert controller.blocked_reason() == "RUNTIME_DEGRADED"

    port.runtime_state = RuntimeSessionState.STOPPED
    assert controller.blocked_reason() == "RUNTIME_NOT_RUNNING"


def test_runtime_safety_controller_blocks_live_startup_and_observation_modes() -> None:
    from qts.runtime.safety_controller import RuntimeSafetyController

    live_port = _FakeSafetyPort(
        runtime_state=RuntimeSessionState.RUNNING,
        mode=RuntimeMode.LIVE,
    )
    assert RuntimeSafetyController(live_port).blocked_reason() == "LIVE_STARTUP_NOT_ALLOWED"

    observation_port = _FakeSafetyPort(
        runtime_state=RuntimeSessionState.RUNNING,
        startup_decision=_StartupDecision(
            order_permission=_OrderPermission(allows_order_submission=False)
        ),
    )
    assert RuntimeSafetyController(observation_port).blocked_reason() == "OBSERVATION_ONLY"

    live_disabled_port = _FakeSafetyPort(
        runtime_state=RuntimeSessionState.RUNNING,
        startup_decision=_StartupDecision(
            order_permission=_OrderPermission(
                allows_order_submission=True,
                allows_live_orders=True,
            ),
            real_order_submission_enabled=False,
        ),
    )
    assert (
        RuntimeSafetyController(live_disabled_port).blocked_reason() == "LIVE_STARTUP_NOT_ALLOWED"
    )
