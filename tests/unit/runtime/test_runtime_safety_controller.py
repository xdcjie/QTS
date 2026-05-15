from __future__ import annotations

from dataclasses import dataclass, field

from qts.runtime.mode import RuntimeMode
from qts.runtime.state import RuntimeSessionState


@dataclass(slots=True)
class _OrderPermission:
    allows_order_submission: bool
    allows_live_orders: bool = False


@dataclass(slots=True)
class _StartupDecision:
    order_permission: _OrderPermission
    real_order_submission_enabled: bool = False


@dataclass(slots=True)
class _Dependencies:
    startup_decision: _StartupDecision | None = None
    mode: RuntimeMode = RuntimeMode.PAPER_SIMULATED


@dataclass(slots=True)
class _Session:
    state: RuntimeSessionState
    _kill_switch_active: bool = False
    _dependencies: _Dependencies = field(default_factory=_Dependencies)


def test_runtime_safety_controller_blocks_with_existing_reason_codes() -> None:
    from qts.runtime.safety_controller import RuntimeSafetyController

    session = _Session(state=RuntimeSessionState.RUNNING)
    controller = RuntimeSafetyController(session)

    session._kill_switch_active = True
    assert controller.blocked_reason() == "KILL_SWITCH_ACTIVE"

    session._kill_switch_active = False
    session.state = RuntimeSessionState.PAUSED
    assert controller.blocked_reason() == "RUNTIME_PAUSED"

    session.state = RuntimeSessionState.DEGRADED
    assert controller.blocked_reason() == "RUNTIME_DEGRADED"

    session.state = RuntimeSessionState.STOPPED
    assert controller.blocked_reason() == "RUNTIME_NOT_RUNNING"


def test_runtime_safety_controller_blocks_live_startup_and_observation_modes() -> None:
    from qts.runtime.safety_controller import RuntimeSafetyController

    live_session = _Session(
        state=RuntimeSessionState.RUNNING,
        _dependencies=_Dependencies(mode=RuntimeMode.LIVE),
    )
    assert RuntimeSafetyController(live_session).blocked_reason() == "LIVE_STARTUP_NOT_ALLOWED"

    observation_session = _Session(
        state=RuntimeSessionState.RUNNING,
        _dependencies=_Dependencies(
            startup_decision=_StartupDecision(
                order_permission=_OrderPermission(allows_order_submission=False)
            )
        ),
    )
    assert RuntimeSafetyController(observation_session).blocked_reason() == "OBSERVATION_ONLY"

    live_disabled_session = _Session(
        state=RuntimeSessionState.RUNNING,
        _dependencies=_Dependencies(
            startup_decision=_StartupDecision(
                order_permission=_OrderPermission(
                    allows_order_submission=True,
                    allows_live_orders=True,
                ),
                real_order_submission_enabled=False,
            )
        ),
    )
    assert (
        RuntimeSafetyController(live_disabled_session).blocked_reason()
        == "LIVE_STARTUP_NOT_ALLOWED"
    )
