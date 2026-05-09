"""Contract specification: tick size, lot size, multiplier, settlement, calendar."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class SettlementType(StrEnum):
    """How a contract settles."""

    CASH = "cash"
    PHYSICAL = "physical"


@dataclass(frozen=True, slots=True)
class ContractSpec:
    """Trading contract metadata required for valuation and order sizing."""

    tick_size: Decimal
    lot_size: Decimal
    multiplier: Decimal
    settlement: SettlementType
    calendar_id: str

    def __post_init__(self) -> None:
        _require_positive(self.tick_size, "tick_size")
        _require_positive(self.lot_size, "lot_size")
        _require_positive(self.multiplier, "multiplier")
        if not self.calendar_id.strip():
            raise ValueError("calendar_id must not be empty")


def _require_positive(value: Decimal, name: str) -> None:
    if value <= Decimal("0"):
        raise ValueError(f"{name} must be positive")


__all__ = ["ContractSpec", "SettlementType"]
