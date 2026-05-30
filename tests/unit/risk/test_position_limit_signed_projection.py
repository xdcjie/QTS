"""Gate tests for signed position-limit projection (DR-007)."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.risk import OrderRiskRequest
from qts.risk.rules.position_limit import PositionLimitRule

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _request(*, current: Decimal, signed_delta: Decimal) -> OrderRiskRequest:
    return OrderRiskRequest(
        instrument_id=_INSTRUMENT,
        quantity=abs(signed_delta),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        current_position=current,
        signed_quantity_delta=signed_delta,
    )


def test_short_then_buy_projects_net_reduced_position() -> None:
    # short 10, buy 5 -> net -5 -> projected 5 (de-risking), within limit 10.
    decision = PositionLimitRule(max_position=Decimal("10")).check(
        _request(current=Decimal("-10"), signed_delta=Decimal("5")),
    )
    assert decision.approved
    assert decision.evidence["projected_position"] == Decimal("5")


def test_long_then_sell_projects_net_reduced_position() -> None:
    # long 10, sell 5 -> net 5 -> projected 5, within limit 10.
    decision = PositionLimitRule(max_position=Decimal("10")).check(
        _request(current=Decimal("10"), signed_delta=Decimal("-5")),
    )
    assert decision.approved
    assert decision.evidence["projected_position"] == Decimal("5")


def test_long_then_buy_projects_increased_position_and_rejects() -> None:
    # long 10, buy 5 -> net 15 -> projected 15, exceeds limit 10.
    decision = PositionLimitRule(max_position=Decimal("10")).check(
        _request(current=Decimal("10"), signed_delta=Decimal("5")),
    )
    assert not decision.approved
    assert decision.reason_code == "POSITION_LIMIT_EXCEEDED"
    assert decision.evidence["projected_position"] == Decimal("15")


def test_de_risking_from_over_limit_position_is_not_blocked() -> None:
    # Already over the limit at 15; selling 5 reduces to 10 -> must be allowed.
    decision = PositionLimitRule(max_position=Decimal("10")).check(
        _request(current=Decimal("15"), signed_delta=Decimal("-5")),
    )
    assert decision.approved
    assert decision.evidence["projected_position"] == Decimal("10")


def test_without_signed_delta_falls_back_to_conservative_worst_case() -> None:
    request = OrderRiskRequest(
        instrument_id=_INSTRUMENT,
        quantity=Decimal("5"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        current_position=Decimal("8"),
    )
    decision = PositionLimitRule(max_position=Decimal("10")).check(request)
    assert not decision.approved
    assert decision.evidence["projected_position"] == Decimal("13")
