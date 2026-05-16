from __future__ import annotations


def test_broker_runtime_startup_gate_requires_decision_for_broker_modes() -> None:
    from qts.runtime.mode import RuntimeMode
    from qts.runtime.startup_gate import BrokerRuntimeStartupGate

    assert (
        BrokerRuntimeStartupGate(mode=RuntimeMode.LIVE, startup_decision=None).blocked_reason()
        == "LIVE_STARTUP_NOT_ALLOWED"
    )
    assert (
        BrokerRuntimeStartupGate(
            mode=RuntimeMode.PAPER_BROKER,
            startup_decision=None,
        ).blocked_reason()
        == "BROKER_STARTUP_NOT_ALLOWED"
    )
    assert (
        BrokerRuntimeStartupGate(
            mode=RuntimeMode.PAPER_SIMULATED,
            startup_decision=None,
        ).blocked_reason()
        is None
    )


def test_broker_runtime_startup_gate_blocks_observation_and_disabled_live_orders() -> None:
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import LiveRuntimeConfig
    from qts.runtime.mode import RuntimeMode
    from qts.runtime.startup_gate import BrokerRuntimeStartupGate

    observation_decision = validate_live_startup(
        LiveRuntimeConfig(
            mode=RuntimeMode.LIVE_OBSERVATION,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
        )
    )

    assert (
        BrokerRuntimeStartupGate(
            mode=RuntimeMode.LIVE_OBSERVATION,
            startup_decision=observation_decision,
        ).blocked_reason()
        == "OBSERVATION_ONLY"
    )
