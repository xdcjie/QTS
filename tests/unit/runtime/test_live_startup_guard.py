from __future__ import annotations

import importlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.runtime.broker_startup import (
    BrokerRuntimeStartupCheck,
    BrokerRuntimeStartupChecklist,
    BrokerRuntimeStartupDecision,
    BrokerRuntimeStartupDecisionStatus,
    validate_live_startup,
)
from qts.runtime.config import BrokerRuntimeConfig
from qts.runtime.live_capital import LiveCapitalEnablementRequest, OperatorSignoff
from qts.runtime.mode import (
    AccountEnvironment,
    ExecutionEnvironment,
    MarketDataEnvironment,
    RuntimeMode,
)
from qts.runtime.permissions import OrderSubmissionPermission


def test_broker_runtime_startup_types_are_canonical() -> None:
    assert BrokerRuntimeStartupCheck.__name__ == "BrokerRuntimeStartupCheck"
    assert BrokerRuntimeStartupChecklist.__name__ == "BrokerRuntimeStartupChecklist"
    assert BrokerRuntimeStartupDecision.__name__ == "BrokerRuntimeStartupDecision"
    assert BrokerRuntimeStartupDecisionStatus.__name__ == "BrokerRuntimeStartupDecisionStatus"
    assert BrokerRuntimeStartupChecklist.__module__ == "qts.runtime.broker_startup"
    assert validate_live_startup.__module__ == "qts.runtime.broker_startup"
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("qts.runtime.live")


def test_live_startup_guard_requires_all_safety_controls_for_live_mode() -> None:
    config = BrokerRuntimeConfig(
        mode=RuntimeMode.LIVE.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=False,
        allow_live_orders=True,
        broker_account_code="DU1234567",
        broker_port=4001,
        operator_signoff_id="ops-approval-1",
    )

    with pytest.raises(ValueError, match="kill_switch_configured"):
        validate_live_startup(config)


def test_live_startup_checklist_reports_evidence_and_remediation() -> None:
    config = BrokerRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=False,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    checklist = BrokerRuntimeStartupChecklist.from_config(config)
    account_check = checklist.by_name("account_configured")

    assert not checklist.passed
    assert account_check.status == "FAIL"
    assert account_check.severity == "BLOCKER"
    assert account_check.evidence == "account_configured=False"
    assert "account" in account_check.remediation


def test_startup_checklist_blocks_only_blocker_severity_failures() -> None:
    checklist = BrokerRuntimeStartupChecklist(
        checks=(
            BrokerRuntimeStartupCheck(
                check_name="operator_note",
                status="FAIL",
                severity="WARNING",
                evidence="operator_note=missing",
                remediation="record optional operator note",
            ),
            BrokerRuntimeStartupCheck(
                check_name="schema_version",
                status="PASS",
                severity="INFO",
                evidence="schema_version=1",
                remediation="none",
            ),
        )
    )
    blocked = BrokerRuntimeStartupChecklist(
        checks=(
            BrokerRuntimeStartupCheck(
                check_name="risk_config_check",
                status="FAIL",
                severity="BLOCKER",
                evidence="risk_configured=False",
                remediation="configure risk limits",
            ),
        )
    )

    assert checklist.passed is True
    assert blocked.passed is False
    assert checklist.to_payload()["checklist_hash"].startswith("sha256:")
    assert checklist.to_payload()["checks"][0]["evidence"] == "operator_note=missing"


def test_live_runtime_config_requires_schema_version() -> None:
    config = BrokerRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert config.schema_version == "1"

    with pytest.raises(ValueError, match="schema_version"):
        BrokerRuntimeConfig(
            mode=RuntimeMode.OBSERVATION.value,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            schema_version=" ",
        )


def test_live_runtime_config_hash_includes_schema_and_environment() -> None:
    config = BrokerRuntimeConfig(
        mode=RuntimeMode.PAPER_BROKER.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        broker_account_code="DUP1234567",
        broker_port=4002,
    )
    changed = replace(config, schema_version="2")

    assert config.to_payload()["schema_version"] == "1"
    assert config.to_payload()["mode"] == "paper_broker"
    assert config.to_payload()["execution_environment"] == "broker"
    assert config.to_payload()["account_environment"] == "paper"
    assert config.config_hash.startswith("sha256:")
    assert changed.config_hash != config.config_hash


def test_paper_simulated_runtime_config_keeps_runtime_mode_enum() -> None:
    from qts.runtime.config.paper import PaperSimulatedRuntimeConfig

    config = PaperSimulatedRuntimeConfig(
        mode=RuntimeMode.PAPER_SIMULATED.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert config.mode is RuntimeMode.PAPER_SIMULATED
    assert config.to_payload()["mode"] == "paper_simulated"


def test_broker_runtime_config_materializes_default_ports() -> None:
    live = BrokerRuntimeConfig(
        mode=RuntimeMode.LIVE.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        allow_live_orders=True,
        broker_account_code="DU1234567",
        operator_signoff_id="ops-approval-1",
    )
    paper = BrokerRuntimeConfig(
        mode=RuntimeMode.PAPER_BROKER.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        broker_account_code="DUP1234567",
    )

    assert live.broker_port == 4001
    assert live.to_payload()["broker_port"] == 4001
    assert paper.broker_port == 4002
    assert paper.to_payload()["broker_port"] == 4002


def test_live_startup_checklist_includes_runtime_safety_gates() -> None:
    config = BrokerRuntimeConfig(
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

    checklist = BrokerRuntimeStartupChecklist.from_config(config)
    check_names = {check.check_name for check in checklist.checks}

    assert {
        "account_mode_check",
        "port_check",
        "api_read_only_check",
        "market_data_permission_check",
        "broker_time_check",
        "open_order_reconciliation_check",
        "position_reconciliation_check",
        "cash_reconciliation_check",
        "risk_config_check",
        "kill_switch_check",
        "event_sink_check",
        "snapshot_store_check",
        "operator_signoff_check",
    } <= check_names
    assert checklist.by_name("market_data_permission_check").status == "FAIL"
    assert checklist.by_name("open_order_reconciliation_check").status == "FAIL"
    assert checklist.by_name("position_reconciliation_check").status == "FAIL"
    assert checklist.by_name("cash_reconciliation_check").status == "FAIL"
    assert checklist.by_name("event_sink_check").status == "FAIL"
    assert checklist.by_name("snapshot_store_check").status == "FAIL"
    assert checklist.by_name("operator_signoff_check").status == "PASS"


def test_startup_checklist_sections_are_independently_observable_and_fail_closed() -> None:
    config = BrokerRuntimeConfig(
        mode=RuntimeMode.LIVE_OBSERVATION.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=False,
        kill_switch_configured=False,
        market_data_permission_live=False,
        open_order_reconciliation_passed=False,
        position_reconciliation_passed=True,
        cash_reconciliation_passed=False,
        event_sink_writable=False,
        snapshot_store_configured=True,
    )

    data_checks = BrokerRuntimeStartupChecklist.data_checks_from_config(config)
    execution_checks = BrokerRuntimeStartupChecklist.execution_checks_from_config(config)
    reconciliation_checks = BrokerRuntimeStartupChecklist.reconciliation_checks_from_config(config)
    capital_checks = BrokerRuntimeStartupChecklist.capital_checks_from_config(config)
    checklist = BrokerRuntimeStartupChecklist.from_config(config)

    assert tuple(check.check_name for check in data_checks) == (
        "market_data_permission_check",
        "broker_time_check",
        "calendar_configured",
    )
    assert "kill_switch_check" in {check.check_name for check in execution_checks}
    assert tuple(check.check_name for check in reconciliation_checks) == (
        "open_order_reconciliation_check",
        "position_reconciliation_check",
        "cash_reconciliation_check",
    )
    assert tuple(check.check_name for check in capital_checks) == (
        "operator_signoff_check",
        "live_capital_signoff_check",
    )
    assert checklist.passed is False

    with pytest.raises(ValueError) as exc_info:
        validate_live_startup(config)

    message = str(exc_info.value)
    assert "market_data_permission_check" in message
    assert "calendar_configured" in message
    assert "kill_switch_check" in message
    assert "open_order_reconciliation_check" in message
    assert "cash_reconciliation_check" in message
    assert "event_sink_check" in message


def test_observation_mode_allows_connections_but_blocks_real_order_submission() -> None:
    config = BrokerRuntimeConfig(
        mode=RuntimeMode.OBSERVATION.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    decision = validate_live_startup(config)

    assert decision.status is BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION
    assert decision.real_order_submission_enabled is False


def test_live_startup_decision_statuses_are_explicit() -> None:
    live_config = BrokerRuntimeConfig(
        mode=RuntimeMode.LIVE.value,
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
    runtime_recovery_decision = validate_live_startup(
        live_config,
        live_capital_request=LiveCapitalEnablementRequest(
            operator_signoff=OperatorSignoff(
                operator_id="operator-1",
                reason="controlled live-capital readiness drill",
                risk_approver_id="risk-1",
                engineering_approver_id="engineering-1",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                strategy_ids=("strategy-a",),
                account_ids=("acct-live-1",),
                max_notional_limit=Decimal("100000"),
                allowed_instruments=("F.US.CME.GC.M2026",),
            ),
            strategy_id="strategy-a",
            account_id="acct-live-1",
            instrument_id="F.US.CME.GC.M2026",
            requested_notional=Decimal("1000"),
        ),
    )
    missing_dual_control_decision = validate_live_startup(live_config)
    paper_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER.value,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DUP1234567",
            broker_port=4002,
        )
    )

    assert runtime_recovery_decision.status is BrokerRuntimeStartupDecisionStatus.ALLOW_LIVE
    assert missing_dual_control_decision.status is (
        BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION
    )
    assert paper_decision.status is BrokerRuntimeStartupDecisionStatus.ALLOW_PAPER
    assert (
        runtime_recovery_decision.order_permission is OrderSubmissionPermission.LIVE_ORDERS_ALLOWED
    )
    assert missing_dual_control_decision.order_permission is (
        OrderSubmissionPermission.OBSERVATION_ONLY
    )
    assert paper_decision.order_permission is OrderSubmissionPermission.PAPER_ORDERS_ALLOWED
    assert runtime_recovery_decision.real_order_submission_enabled is True
    assert missing_dual_control_decision.real_order_submission_enabled is False
    assert paper_decision.real_order_submission_enabled is False


def test_live_observation_mode_uses_explicit_order_permission() -> None:
    config = BrokerRuntimeConfig(
        mode=RuntimeMode.LIVE_OBSERVATION,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    decision = validate_live_startup(config)

    assert config.mode is RuntimeMode.LIVE_OBSERVATION
    assert decision.status is BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION
    assert decision.order_permission is OrderSubmissionPermission.OBSERVATION_ONLY
    assert decision.real_order_submission_enabled is False


def test_live_rejects_paper_account_code() -> None:
    with pytest.raises(ValueError, match="live mode cannot use a paper account"):
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DUP1234567",
            broker_account_kind="paper",
            broker_port=4001,
            operator_signoff_id="ops-approval-1",
        )


def test_paper_broker_rejects_live_account_code() -> None:
    with pytest.raises(ValueError, match="paper broker mode requires a paper account"):
        BrokerRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DU1234567",
            broker_account_kind="live",
            broker_port=4002,
        )


def test_live_requires_operator_signoff_and_explicit_live_orders() -> None:
    with pytest.raises(ValueError, match="operator_signoff_id"):
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU1234567",
            broker_port=4001,
        )

    with pytest.raises(ValueError, match="allow_live_orders"):
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DU1234567",
            broker_port=4001,
            operator_signoff_id="ops-approval-1",
        )


def test_live_uses_default_port_unless_override_reason_is_recorded() -> None:
    with pytest.raises(ValueError, match="broker_port_override_reason"):
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU1234567",
            broker_port=7496,
            operator_signoff_id="ops-approval-1",
        )


def test_paper_simulated_runtime_uses_simulated_execution_environment() -> None:
    from qts.runtime.config.paper import PaperSimulatedRuntimeConfig

    config = PaperSimulatedRuntimeConfig(
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


def test_paper_runtime_configs_have_disjoint_semantics() -> None:
    from qts.runtime.config.paper import PaperSimulatedRuntimeConfig

    broker = BrokerRuntimeConfig(
        mode=RuntimeMode.PAPER_BROKER,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        broker_account_code="DUP1234567",
    )
    simulated = PaperSimulatedRuntimeConfig(
        mode=RuntimeMode.PAPER_SIMULATED,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert broker.execution_environment is ExecutionEnvironment.BROKER
    assert broker.account_environment is AccountEnvironment.PAPER
    assert broker.broker_account_kind == "paper"
    assert broker.broker_port == 4002
    assert simulated.execution_environment is ExecutionEnvironment.SIMULATED
    assert simulated.account_environment is AccountEnvironment.SIMULATED
    assert simulated.broker_account_kind == "simulated"
    assert simulated.broker_port is None

    with pytest.raises(ValueError, match="BrokerRuntimeConfig mode cannot be paper_simulated"):
        BrokerRuntimeConfig(
            mode=RuntimeMode.PAPER_SIMULATED,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
        )
    with pytest.raises(
        ValueError, match="PaperSimulatedRuntimeConfig mode must be paper_simulated"
    ):
        PaperSimulatedRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DUP1234567",
        )


def test_permission_mode_label_is_not_runtime_mode_alias() -> None:
    with pytest.raises(ValueError, match="Unsupported runtime mode"):
        BrokerRuntimeConfig(
            mode=OrderSubmissionPermission.PAPER_ORDERS_ALLOWED.value,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DUP1234567",
            broker_port=4002,
        )
