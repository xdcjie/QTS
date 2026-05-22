"""Position domain value objects."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum


class PositionSide(StrEnum):
    """Directional side of a non-flat signed position quantity."""

    LONG = "long"
    SHORT = "short"

    @property
    def sign(self) -> Decimal:
        """Return the signed-quantity multiplier for this side."""
        return Decimal("1") if self is PositionSide.LONG else Decimal("-1")

    @classmethod
    def from_quantity(cls, quantity: Decimal) -> PositionSide | None:
        """Return the position side implied by signed quantity, or None when flat."""
        if quantity > Decimal("0"):
            return cls.LONG
        if quantity < Decimal("0"):
            return cls.SHORT
        return None

    @classmethod
    def same_for_quantities(cls, left: Decimal, right: Decimal) -> bool:
        """Return whether two signed quantities share a non-flat position side."""
        left_side = cls.from_quantity(left)
        right_side = cls.from_quantity(right)
        return left_side is not None and left_side is right_side

    def opposite(self) -> PositionSide:
        """Return the opposite non-flat position side."""
        return PositionSide.SHORT if self is PositionSide.LONG else PositionSide.LONG


__all__ = ["PositionSide"]
