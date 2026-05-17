from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.risk import OrderRiskRequest


def _request(*, quantity: str, current_position: str = "0") -> OrderRiskRequest:
    return OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal(quantity),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        current_position=Decimal(current_position),
    )


def test_position_limit_rejects_order_that_would_exceed_absolute_position() -> None:
    from qts.risk.rules.position_limit import PositionLimitRule

    decision = PositionLimitRule(max_position=Decimal("100")).check(
        _request(quantity="25", current_position="80")
    )

    assert not decision.approved
    assert decision.reason_code == "POSITION_LIMIT_EXCEEDED"
    assert decision.rule_id == "position_limit"
    assert decision.evidence["projected_position"] == Decimal("105")


def test_position_limit_approves_order_within_absolute_position_limit() -> None:
    from qts.risk.rules.position_limit import PositionLimitRule

    decision = PositionLimitRule(max_position=Decimal("100")).check(
        _request(quantity="20", current_position="-60")
    )

    assert decision.approved
    assert decision.rule_id == "position_limit"
