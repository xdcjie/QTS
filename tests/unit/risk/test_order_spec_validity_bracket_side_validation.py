"""QTS-FINAL-014: OrderSpecValidityRule validates bracket legs vs parent intent."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.orders import BracketLeg, BracketSpec, OrderSide, OrderSpec, OrderType
from qts.domain.risk import OrderRiskRequest
from qts.risk.rules.order_spec_validity import OrderSpecValidityRule

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _bracket(side: OrderSide, *, quantity: Decimal = Decimal("1")) -> OrderSpec:
    return OrderSpec(
        order_type=OrderType.BRACKET,
        bracket=BracketSpec(
            legs=(
                BracketLeg(
                    order_type=OrderType.LIMIT,
                    side=side,
                    quantity=quantity,
                    limit_price=Decimal("110"),
                ),
                BracketLeg(
                    order_type=OrderType.STOP,
                    side=side,
                    quantity=quantity,
                    stop_price=Decimal("90"),
                ),
            )
        ),
    )


def _request(spec: OrderSpec, *, signed_delta: Decimal | None) -> OrderRiskRequest:
    return OrderRiskRequest(
        instrument_id=_INSTRUMENT,
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        order_spec=spec,
        signed_quantity_delta=signed_delta,
    )


def test_long_parent_with_sell_exits_is_approved() -> None:
    decision = OrderSpecValidityRule().check(
        _request(_bracket(OrderSide.SELL), signed_delta=Decimal("1"))
    )
    assert decision.approved


def test_short_parent_with_buy_exits_is_approved() -> None:
    decision = OrderSpecValidityRule().check(
        _request(_bracket(OrderSide.BUY), signed_delta=Decimal("-1"))
    )
    assert decision.approved


def test_long_parent_with_buy_exits_is_rejected() -> None:
    decision = OrderSpecValidityRule().check(
        _request(_bracket(OrderSide.BUY), signed_delta=Decimal("1"))
    )
    assert not decision.approved
    assert decision.reason_code == "INVALID_BRACKET_LEGS"


def test_short_parent_with_sell_exits_is_rejected() -> None:
    decision = OrderSpecValidityRule().check(
        _request(_bracket(OrderSide.SELL), signed_delta=Decimal("-1"))
    )
    assert not decision.approved
    assert decision.reason_code == "INVALID_BRACKET_LEGS"


def test_bracket_leg_quantity_must_match_parent() -> None:
    decision = OrderSpecValidityRule().check(
        _request(_bracket(OrderSide.SELL, quantity=Decimal("2")), signed_delta=Decimal("1"))
    )
    assert not decision.approved
    assert decision.reason_code == "INVALID_BRACKET_LEGS"


def test_mixed_side_exit_legs_are_rejected() -> None:
    spec = OrderSpec(
        order_type=OrderType.BRACKET,
        bracket=BracketSpec(
            legs=(
                BracketLeg(
                    order_type=OrderType.LIMIT,
                    side=OrderSide.SELL,
                    quantity=Decimal("1"),
                    limit_price=Decimal("110"),
                ),
                BracketLeg(
                    order_type=OrderType.STOP,
                    side=OrderSide.BUY,
                    quantity=Decimal("1"),
                    stop_price=Decimal("90"),
                ),
            )
        ),
    )
    decision = OrderSpecValidityRule().check(_request(spec, signed_delta=Decimal("1")))
    assert not decision.approved
    assert decision.reason_code == "INVALID_BRACKET_LEGS"
