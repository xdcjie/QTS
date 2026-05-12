"""Position book keyed by internal instrument IDs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from qts.core.ids import InstrumentId


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable position snapshot."""

    instrument_id: InstrumentId
    quantity: Decimal


class PositionBook:
    """Mutable position book intended to be owned by AccountActor later."""

    def __init__(self, positions: Mapping[InstrumentId, Decimal] | None = None) -> None:
        """Perform __init__."""
        self._positions = dict(positions or {})

    def apply_delta(self, instrument_id: InstrumentId, quantity_delta: Decimal) -> None:
        """Perform apply_delta."""
        self._positions[instrument_id] = self.quantity(instrument_id) + quantity_delta

    def quantity(self, instrument_id: InstrumentId) -> Decimal:
        """Perform quantity."""
        return self._positions.get(instrument_id, Decimal("0"))

    def snapshot(self) -> Mapping[InstrumentId, Position]:
        """Perform snapshot."""
        return MappingProxyType(
            {
                instrument_id: Position(instrument_id=instrument_id, quantity=quantity)
                for instrument_id, quantity in self._positions.items()
            }
        )


__all__ = ["Position", "PositionBook"]
