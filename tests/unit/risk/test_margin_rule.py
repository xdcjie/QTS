"""Gate tests for the pre-trade margin limit rule (DR-005)."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.risk import OrderRiskRequest, RiskDecisionStatus
from qts.risk.rules.margin_limit import MarginRule

_INSTRUMENT = InstrumentId("FUTURE.US.COMEX.GC")


def _request(
    *,
    projected: Decimal | None,
    available: Decimal | None,
    current: Decimal | None = Decimal("0"),
) -> OrderRiskRequest:
    return OrderRiskRequest(
        instrument_id=_INSTRUMENT,
        quantity=Decimal("1"),
        price=Decimal("2000"),
        multiplier=Decimal("100"),
        current_margin_requirement=current,
        projected_initial_margin=projected,
        available_margin=available,
    )


def test_margin_rule_rejects_order_exceeding_available_margin() -> None:
    decision = MarginRule().check(
        _request(projected=Decimal("12000"), available=Decimal("10000"), current=Decimal("5000")),
    )
    assert decision.status is RiskDecisionStatus.REJECTED
    assert decision.reason_code == "MARGIN_LIMIT_EXCEEDED"
    assert decision.evidence["current_margin"] == Decimal("5000")
    assert decision.evidence["projected_margin"] == Decimal("12000")
    assert decision.evidence["available_margin"] == Decimal("10000")


def test_margin_rule_approves_order_within_available_margin() -> None:
    decision = MarginRule().check(
        _request(projected=Decimal("8000"), available=Decimal("10000"), current=Decimal("5000")),
    )
    assert decision.approved
    assert decision.evidence["projected_margin"] == Decimal("8000")


def test_margin_rule_approves_risk_reducing_order_with_zero_incremental_margin() -> None:
    # A position-reducing order has zero incremental margin and must pass even
    # when free margin headroom is small.
    decision = MarginRule().check(
        _request(projected=Decimal("0"), available=Decimal("1"), current=Decimal("9999")),
    )
    assert decision.approved


def test_margin_rule_fails_closed_when_margin_context_missing() -> None:
    decision = MarginRule().check(_request(projected=None, available=None))
    assert decision.status is RiskDecisionStatus.REJECTED
    assert decision.reason_code == "MARGIN_CONTEXT_REQUIRED"
