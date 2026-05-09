from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest


def test_risk_decision_approved_and_rejected_are_explicit() -> None:
    from qts.domain.risk import RiskDecision, RiskDecisionStatus

    approved = RiskDecision.approve()
    rejected = RiskDecision.rejected("MAX_QTY_EXCEEDED", "order quantity exceeds limit")

    assert approved.status is RiskDecisionStatus.APPROVED
    assert approved.approved
    assert rejected.status is RiskDecisionStatus.REJECTED
    assert not rejected.approved
    assert rejected.reason_code == "MAX_QTY_EXCEEDED"
    assert rejected.reason == "order quantity exceeds limit"
    assert rejected.reason_text == "order quantity exceeds limit"
    with pytest.raises(FrozenInstanceError):
        rejected.reason = "changed"  # type: ignore[misc]


def test_risk_decision_carries_audit_fields() -> None:
    from qts.domain.risk import RiskDecision

    checked_at = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    decision = RiskDecision.rejected(
        "BLOCKED",
        "blocked by test",
        rule_id="rule-001",
        checked_at=checked_at,
    )

    assert decision.rule_id == "rule-001"
    assert decision.checked_at == checked_at


def test_risk_engine_returns_first_rejection_without_silent_failure() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.risk import OrderRiskRequest, RiskDecision
    from qts.risk.risk_engine import RiskEngine

    class ApprovingRule:
        def check(self, request: OrderRiskRequest) -> RiskDecision:
            return RiskDecision.approve()

    class RejectingRule:
        def check(self, request: OrderRiskRequest) -> RiskDecision:
            return RiskDecision.rejected("BLOCKED", "blocked by test")

    request = OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
    )

    decision = RiskEngine([ApprovingRule(), RejectingRule()]).check(request)

    assert not decision.approved
    assert decision.reason_code == "BLOCKED"
