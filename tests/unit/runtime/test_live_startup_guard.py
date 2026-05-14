from __future__ import annotations

from dataclasses import replace

import pytest
from qts.runtime.config import LiveRuntimeConfig
from qts.runtime.live import (
    LivePermissionMode,
    LiveStartupChecklist,
    LiveStartupDecisionStatus,
    validate_live_startup,
)
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


def test_live_startup_checklist_reports_evidence_and_remediation() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=False,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    checklist = LiveStartupChecklist.from_config(config)
    account_check = checklist.by_name("account_configured")

    assert not checklist.passed
    assert account_check.status == "FAIL"
    assert account_check.severity == "BLOCKER"
    assert account_check.evidence == "account_configured=False"
    assert "account" in account_check.remediation


def test_live_runtime_config_requires_schema_version() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert config.schema_version == "1"

    with pytest.raises(ValueError, match="schema_version"):
        LiveRuntimeConfig(
            mode=RuntimeMode.OBSERVATION.value,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            schema_version=" ",
        )


def test_live_runtime_config_hash_includes_schema_and_environment() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.PAPER_BROKER.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        broker_account_code="DU1234567",
        broker_port=4002,
    )
    changed = replace(config, schema_version="2")

    assert config.to_payload()["schema_version"] == "1"
    assert config.to_payload()["mode"] == "paper_broker"
    assert config.to_payload()["execution_environment"] == "broker"
    assert config.to_payload()["account_environment"] == "paper"
    assert config.config_hash.startswith("sha256:")
    assert changed.config_hash != config.config_hash


def test_live_startup_checklist_includes_runtime_safety_gates() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        market_data_permission_live=False,
        reconciliation_passed=False,
        event_sink_writable=False,
        snapshot_store_configured=False,
    )

    checklist = LiveStartupChecklist.from_config(config)

    assert checklist.by_name("market_data_permission_check").status == "FAIL"
    assert checklist.by_name("reconciliation_check").status == "FAIL"
    assert checklist.by_name("event_sink_check").status == "FAIL"
    assert checklist.by_name("snapshot_store_check").status == "FAIL"
    assert checklist.by_name("operator_signoff_check").status == "PASS"


def test_observation_mode_allows_connections_but_blocks_real_order_submission() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    decision = validate_live_startup(config)

    assert decision.status is LiveStartupDecisionStatus.ALLOW_OBSERVATION
    assert decision.real_order_submission_enabled is False


def test_live_startup_decision_statuses_are_explicit() -> None:
    live_decision = validate_live_startup(
        LiveRuntimeConfig(
            mode=RuntimeMode.LIVE.value,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="U1234567",
            broker_port=4001,
            operator_signoff_id="ops-approval-1",
        )
    )
    paper_decision = validate_live_startup(
        LiveRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER.value,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DU1234567",
            broker_port=4002,
        )
    )

    assert live_decision.status is LiveStartupDecisionStatus.ALLOW_LIVE
    assert paper_decision.status is LiveStartupDecisionStatus.ALLOW_PAPER
    assert live_decision.real_order_submission_enabled is True
    assert paper_decision.real_order_submission_enabled is False


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


def test_permission_mode_label_is_not_runtime_mode_alias() -> None:
    with pytest.raises(ValueError, match="Unsupported runtime mode"):
        LiveRuntimeConfig(
            mode=LivePermissionMode.PAPER.value,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DU1234567",
            broker_port=4002,
        )
