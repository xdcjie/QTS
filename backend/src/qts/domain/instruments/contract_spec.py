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
    """Trading contract metadata required for valuation and order sizing.

    ``initial_margin_rate`` is a per-contract product fact: the fraction of
    notional posted as initial margin (e.g. ``Decimal("0.05")``). It is
    ``None`` for cash instruments. Tradable futures must carry a configured
    value; runtime/backtest margin policy fails closed when a tradable futures
    contract reaches risk without this product fact.
    """

    tick_size: Decimal
    lot_size: Decimal
    multiplier: Decimal
    settlement: SettlementType
    calendar_id: str
    initial_margin_rate: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate positive sizing fields, calendar id, and margin rate bounds."""
        self._require_positive(self.tick_size, "tick_size")
        self._require_positive(self.lot_size, "lot_size")
        self._require_positive(self.multiplier, "multiplier")
        if not self.calendar_id.strip():
            raise ValueError("calendar_id must not be empty")
        if self.initial_margin_rate is not None:
            self._require_positive(self.initial_margin_rate, "initial_margin_rate")
            if self.initial_margin_rate > Decimal("1"):
                raise ValueError("initial_margin_rate must not exceed 1")

    @staticmethod
    def _require_positive(value: Decimal, name: str) -> None:
        """Raise when ``value`` is not strictly positive."""
        if value <= Decimal("0"):
            raise ValueError(f"{name} must be positive")


__all__ = ["ContractSpec", "SettlementType"]
