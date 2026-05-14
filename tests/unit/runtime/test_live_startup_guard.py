from __future__ import annotations

import pytest
from qts.runtime.config import LiveRuntimeConfig
from qts.runtime.live import LivePermissionMode, validate_live_startup
from qts.runtime.mode import (
    AccountEnvironment,
    ExecutionEnvironment,
    MarketDataEnvironment,
    RuntimeMode,
)


def test_live_startup_guard_requires_all_safety_controls_for_live_mode() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.LIVE.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=False,
        allow_live_orders=True,
        broker_account_code="U1234567",
        broker_port=4001,
        operator_signoff_id="ops-approval-1",
    )

    with pytest.raises(ValueError, match="kill_switch_configured"):
        validate_live_startup(config)


def test_observation_mode_allows_connections_but_blocks_real_order_submission() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert validate_live_startup(config).real_order_submission_enabled is False


def test_live_rejects_paper_account_code() -> None:
    with pytest.raises(ValueError, match="live mode cannot use a paper account"):
        LiveRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU1234567",
            broker_port=4001,
            operator_signoff_id="ops-approval-1",
        )


def test_paper_broker_rejects_live_account_code() -> None:
    with pytest.raises(ValueError, match="paper broker mode requires a paper account"):
        LiveRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="U1234567",
            broker_port=4002,
        )


def test_live_requires_operator_signoff_and_explicit_live_orders() -> None:
    with pytest.raises(ValueError, match="operator_signoff_id"):
        LiveRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="U1234567",
            broker_port=4001,
        )

    with pytest.raises(ValueError, match="allow_live_orders"):
        LiveRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="U1234567",
            broker_port=4001,
            operator_signoff_id="ops-approval-1",
        )


def test_live_uses_default_port_unless_override_reason_is_recorded() -> None:
    with pytest.raises(ValueError, match="broker_port_override_reason"):
        LiveRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="U1234567",
            broker_port=7496,
            operator_signoff_id="ops-approval-1",
        )


def test_paper_simulated_runtime_uses_simulated_execution_environment() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.PAPER_SIMULATED,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        market_data_environment=MarketDataEnvironment.REALTIME,
    )

    assert config.execution_environment is ExecutionEnvironment.SIMULATED
    assert config.account_environment is AccountEnvironment.SIMULATED
    assert validate_live_startup(config).real_order_submission_enabled is False


def test_legacy_paper_mode_maps_to_paper_broker() -> None:
    config = LiveRuntimeConfig(
        mode=LivePermissionMode.PAPER.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        broker_account_code="DU1234567",
        broker_port=4002,
    )

    assert config.mode == RuntimeMode.PAPER_BROKER.value
    assert config.execution_environment is ExecutionEnvironment.BROKER
    assert config.account_environment is AccountEnvironment.PAPER
