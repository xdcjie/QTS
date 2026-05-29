"""Futures margin requirement calculator."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding


@dataclass(frozen=True, slots=True)
class MarginRequirement:
    """Immutable margin requirement snapshot."""

    initial_margin: Decimal
    maintenance_margin: Decimal
    available_margin: Decimal


class MarginCalculator:
    """Compute futures margin requirements from positions and contract specs."""

    def __init__(
        self,
        *,
        initial_margin_rate: Decimal = Decimal("0.05"),
        maintenance_margin_rate: Decimal = Decimal("0.04"),
    ) -> None:
        """Perform __init__."""
        if initial_margin_rate <= Decimal("0"):
            raise ValueError("initial_margin_rate must be positive")
        if maintenance_margin_rate <= Decimal("0"):
            raise ValueError("maintenance_margin_rate must be positive")
        if maintenance_margin_rate > initial_margin_rate:
            raise ValueError("maintenance_margin_rate must not exceed initial_margin_rate")
        self._initial_margin_rate = initial_margin_rate
        self._maintenance_margin_rate = maintenance_margin_rate

    def margin_requirement(
        self,
        positions: Mapping[InstrumentId, Holding],
        marks: Mapping[InstrumentId, Decimal],
        multipliers: Mapping[InstrumentId, Decimal],
        account_equity: Decimal,
    ) -> MarginRequirement:
        """Compute initial and maintenance margin requirements.

        For each position: notional = abs(quantity) * mark_price * multiplier.
        initial_margin = sum(notional * initial_margin_rate).
        maintenance_margin = sum(notional * maintenance_margin_rate).
        available_margin = account_equity - initial_margin.
        """
        initial_margin = Decimal("0")
        maintenance_margin = Decimal("0")

        for instrument_id, holding in positions.items():
            mark = marks.get(instrument_id)
            multiplier = multipliers.get(instrument_id, Decimal("1"))
            if mark is None or holding.quantity == Decimal("0"):
                continue
            notional = abs(holding.quantity) * mark * multiplier
            initial_margin += notional * self._initial_margin_rate
            maintenance_margin += notional * self._maintenance_margin_rate

        available_margin = account_equity - initial_margin

        return MarginRequirement(
            initial_margin=initial_margin,
            maintenance_margin=maintenance_margin,
            available_margin=available_margin,
        )


__all__ = ["MarginCalculator", "MarginRequirement"]
