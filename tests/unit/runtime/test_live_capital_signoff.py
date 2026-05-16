from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.runtime.broker_startup import BrokerRuntimeStartupDecisionStatus, validate_live_startup
from qts.runtime.config import BrokerRuntimeConfig
from qts.runtime.live_capital import (
    LiveCapitalEnablementRequest,
    OperatorSignoff,
)
from qts.runtime.mode import RuntimeMode
from qts.runtime.permissions import OrderSubmissionPermission


def _live_config() -> BrokerRuntimeConfig:
    return BrokerRuntimeConfig(
        mode=RuntimeMode.LIVE,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        allow_live_orders=True,
        broker_account_code="DU1234567",
        broker_port=4001,
        operator_signoff_id="ops-signoff-1",
    )


def _signoff(*, expires_at: datetime | None = None) -> OperatorSignoff:
    return OperatorSignoff(
        operator_id="operator-1",
        reason="controlled live-capital readiness drill",
        risk_approver_id="risk-1",
        engineering_approver_id="engineering-1",
        expires_at=expires_at or datetime(2026, 5, 17, tzinfo=UTC),
        strategy_ids=("strategy-a",),
        account_ids=("acct-live-1",),
        max_notional_limit=Decimal("100000"),
        allowed_instruments=("F.US.CME.GC.M2026",),
    )


def test_live_capital_requires_operator_and_risk_signoff() -> None:
    request = LiveCapitalEnablementRequest(
        operator_signoff=OperatorSignoff(
            operator_id="operator-1",
            reason="controlled live-capital readiness drill",
            risk_approver_id="",
            engineering_approver_id="engineering-1",
            expires_at=datetime(2026, 5, 17, tzinfo=UTC),
            strategy_ids=("strategy-a",),
            account_ids=("acct-live-1",),
            max_notional_limit=Decimal("100000"),
            allowed_instruments=("F.US.CME.GC.M2026",),
        ),
        strategy_id="strategy-a",
        account_id="acct-live-1",
        instrument_id="F.US.CME.GC.M2026",
        requested_notional=Decimal("1000"),
    )

    decision = request.evaluate(now=datetime(2026, 5, 16, tzinfo=UTC))

    assert decision.allowed is False
    assert decision.order_permission is OrderSubmissionPermission.OBSERVATION_ONLY
    assert "risk_approver_id" in decision.reason


def test_expired_signoff_blocks_live_orders() -> None:
    request = LiveCapitalEnablementRequest(
        operator_signoff=_signoff(expires_at=datetime(2026, 5, 15, tzinfo=UTC)),
        strategy_id="strategy-a",
        account_id="acct-live-1",
        instrument_id="F.US.CME.GC.M2026",
        requested_notional=Decimal("1000"),
    )

    decision = request.evaluate(now=datetime(2026, 5, 16, tzinfo=UTC))
    startup = validate_live_startup(_live_config(), live_capital_request=request)

    assert decision.allowed is False
    assert decision.order_permission is OrderSubmissionPermission.OBSERVATION_ONLY
    assert "expired" in decision.reason
    assert startup.status is BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION
    assert startup.real_order_submission_enabled is False
    assert startup.order_permission is OrderSubmissionPermission.OBSERVATION_ONLY


def test_signoff_scope_blocks_unapproved_strategy() -> None:
    request = LiveCapitalEnablementRequest(
        operator_signoff=_signoff(),
        strategy_id="strategy-b",
        account_id="acct-live-1",
        instrument_id="F.US.CME.GC.M2026",
        requested_notional=Decimal("1000"),
    )

    decision = request.evaluate(now=datetime(2026, 5, 16, tzinfo=UTC))

    assert decision.allowed is False
    assert decision.order_permission is OrderSubmissionPermission.OBSERVATION_ONLY
    assert "strategy_id" in decision.reason


def test_signoff_scope_blocks_unapproved_account() -> None:
    request = LiveCapitalEnablementRequest(
        operator_signoff=_signoff(),
        strategy_id="strategy-a",
        account_id="acct-live-2",
        instrument_id="F.US.CME.GC.M2026",
        requested_notional=Decimal("1000"),
    )

    decision = request.evaluate(now=datetime(2026, 5, 16, tzinfo=UTC))

    assert decision.allowed is False
    assert decision.order_permission is OrderSubmissionPermission.OBSERVATION_ONLY
    assert "account_id" in decision.reason


def test_valid_signoff_keeps_live_permission_with_startup_evidence() -> None:
    request = LiveCapitalEnablementRequest(
        operator_signoff=_signoff(expires_at=datetime.now(UTC) + timedelta(hours=1)),
        strategy_id="strategy-a",
        account_id="acct-live-1",
        instrument_id="F.US.CME.GC.M2026",
        requested_notional=Decimal("1000"),
    )

    startup = validate_live_startup(_live_config(), live_capital_request=request)
    signoff_check = startup.checklist.by_name("live_capital_signoff_check")

    assert startup.status is BrokerRuntimeStartupDecisionStatus.ALLOW_LIVE
    assert startup.order_permission is OrderSubmissionPermission.LIVE_ORDERS_ALLOWED
    assert startup.real_order_submission_enabled is True
    assert signoff_check.status == "PASS"
    assert "operator_id=operator-1" in signoff_check.evidence
    assert "risk_approver_id=risk-1" in signoff_check.evidence
