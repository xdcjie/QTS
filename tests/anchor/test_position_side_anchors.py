from __future__ import annotations

from decimal import Decimal


def test_position_side_from_signed_quantity() -> None:
    from qts.domain.positions import PositionSide

    assert PositionSide.from_quantity(Decimal("2")) is PositionSide.LONG
    assert PositionSide.from_quantity(Decimal("-2")) is PositionSide.SHORT
    assert PositionSide.from_quantity(Decimal("0")) is None


def test_position_side_exposes_directional_sign() -> None:
    from qts.domain.positions import PositionSide

    assert PositionSide.LONG.sign == Decimal("1")
    assert PositionSide.SHORT.sign == Decimal("-1")


def test_position_side_opposite() -> None:
    from qts.domain.positions import PositionSide

    assert PositionSide.LONG.opposite() is PositionSide.SHORT
    assert PositionSide.SHORT.opposite() is PositionSide.LONG


def test_position_side_same_for_quantities_requires_non_flat_same_side() -> None:
    from qts.domain.positions import PositionSide

    assert PositionSide.same_for_quantities(Decimal("2"), Decimal("3")) is True
    assert PositionSide.same_for_quantities(Decimal("-2"), Decimal("-3")) is True
    assert PositionSide.same_for_quantities(Decimal("2"), Decimal("-3")) is False
    assert PositionSide.same_for_quantities(Decimal("0"), Decimal("3")) is False
    assert PositionSide.same_for_quantities(Decimal("0"), Decimal("0")) is False
