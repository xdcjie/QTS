"""QTS-FINAL-014: BracketLeg.side is the typed OrderSide enum, not a str."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

import pytest
from qts.domain.orders import BracketLeg, OrderSide, OrderType


def test_bracket_leg_side_is_order_side_enum() -> None:
    leg = BracketLeg(
        order_type=OrderType.LIMIT,
        side=OrderSide.SELL,
        quantity=Decimal("1"),
        limit_price=Decimal("100"),
    )
    assert leg.side is OrderSide.SELL


def test_bracket_leg_coerces_serialized_side_value() -> None:
    # The serialized value is coerced to the enum; deliberately pass a str.
    leg = BracketLeg(
        order_type=OrderType.STOP,
        side="buy",  # type: ignore[arg-type]
        quantity=Decimal("1"),
        stop_price=Decimal("90"),
    )
    assert leg.side is OrderSide.BUY


def test_bracket_leg_rejects_unknown_side() -> None:
    with pytest.raises(ValueError):
        BracketLeg(
            order_type=OrderType.LIMIT,
            side="hold",  # type: ignore[arg-type]
            quantity=Decimal("1"),
            limit_price=Decimal("100"),
        )


def test_bracket_leg_payload_serializes_side_value() -> None:
    from qts.domain.orders import BracketSpec, OrderSpec

    spec = OrderSpec(
        order_type=OrderType.BRACKET,
        bracket=BracketSpec(
            legs=(
                BracketLeg(
                    order_type=OrderType.LIMIT,
                    side=OrderSide.BUY,
                    quantity=Decimal("2"),
                    limit_price=Decimal("100"),
                ),
                BracketLeg(
                    order_type=OrderType.STOP,
                    side=OrderSide.BUY,
                    quantity=Decimal("2"),
                    stop_price=Decimal("110"),
                ),
            )
        ),
    )
    legs = cast(list[dict[str, object]], spec.to_payload()["bracket_legs"])
    assert [leg["side"] for leg in legs] == ["buy", "buy"]
