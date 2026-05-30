"""Derivative metadata for futures and options."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from qts.core.ids import InstrumentId


class OptionRight(StrEnum):
    """Option payoff direction."""

    CALL = "call"
    PUT = "put"


class ExerciseStyle(StrEnum):
    """Option exercise style."""

    AMERICAN = "american"
    EUROPEAN = "european"


@dataclass(frozen=True, slots=True)
class DerivativeSpec:
    """Common derivative metadata."""

    expiry: date
    underlying: InstrumentId


@dataclass(frozen=True, slots=True)
class FutureSpec(DerivativeSpec):
    """Future contract metadata."""

    root_symbol: str

    def __post_init__(self) -> None:
        """Validate that the future root symbol is non-empty."""
        if not self.root_symbol.strip():
            raise ValueError("root_symbol must not be empty")


@dataclass(frozen=True, slots=True)
class OptionSpec(DerivativeSpec):
    """Option contract metadata."""

    strike: Decimal
    right: OptionRight
    exercise_style: ExerciseStyle = ExerciseStyle.AMERICAN

    def __post_init__(self) -> None:
        """Validate that the option strike is positive."""
        if self.strike <= Decimal("0"):
            raise ValueError("strike must be positive")


__all__ = [
    "DerivativeSpec",
    "ExerciseStyle",
    "FutureSpec",
    "OptionRight",
    "OptionSpec",
]
