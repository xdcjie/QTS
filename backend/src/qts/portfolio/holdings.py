"""Average-cost holdings owned by account state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType

from qts.core.ids import InstrumentId


class CostBasisMethod(StrEnum):
    """Supported holding cost basis convention."""

    AVERAGE = "average"


@dataclass(frozen=True, slots=True)
class Holding:
    """Immutable holding snapshot using average-cost accounting.

    Commission is accounted as cash movement, not as part of average cost.
    """

    instrument_id: InstrumentId
    quantity: Decimal
    average_cost: Decimal
    realized_pnl: Decimal
    cost_basis_method: CostBasisMethod = CostBasisMethod.AVERAGE
    opened_at: datetime | None = None
    last_fill_at: datetime | None = None

    def market_value(self, mark_price: Decimal, multiplier: Decimal) -> Decimal:
        """Return signed market value at the supplied mark."""
        return self.quantity * mark_price * multiplier

    def unrealized_pnl(self, mark_price: Decimal, multiplier: Decimal) -> Decimal:
        """Return unrealized PnL at the supplied mark."""
        if self.quantity == Decimal("0"):
            return Decimal("0")
        sign = Decimal("1") if self.quantity > Decimal("0") else Decimal("-1")
        return abs(self.quantity) * (mark_price - self.average_cost) * sign * multiplier

    def holding_period(self, now: datetime) -> timedelta:
        """Return elapsed time since the holding opened."""
        if self.opened_at is None:
            return timedelta(0)
        return now - self.opened_at


@dataclass(frozen=True, slots=True)
class PositionClosed:
    """Runtime accounting event emitted when a holding reaches flat."""

    instrument_id: InstrumentId
    closed_quantity: Decimal
    exit_price: Decimal
    realized_pnl: Decimal
    opened_at: datetime | None
    closed_at: datetime


class HoldingBook:
    """Mutable average-cost holding book."""

    def __init__(self, holdings: Mapping[InstrumentId, Holding] | None = None) -> None:
        self._holdings: dict[InstrumentId, Holding] = dict(holdings or {})

    def holding(self, instrument_id: InstrumentId) -> Holding:
        """Return the current holding or a flat zero-cost snapshot."""
        return self._holdings.get(
            instrument_id,
            Holding(
                instrument_id=instrument_id,
                quantity=Decimal("0"),
                average_cost=Decimal("0"),
                realized_pnl=Decimal("0"),
            ),
        )

    def quantity(self, instrument_id: InstrumentId) -> Decimal:
        """Return signed quantity for order planning."""
        return self.holding(instrument_id).quantity

    def apply_fill(
        self,
        *,
        instrument_id: InstrumentId,
        signed_quantity: Decimal,
        price: Decimal,
        multiplier: Decimal,
        fill_time: datetime | None = None,
    ) -> tuple[PositionClosed, ...]:
        """Apply one signed fill and return close events."""
        if signed_quantity == Decimal("0"):
            raise ValueError("signed_quantity must not be zero")
        if price < Decimal("0"):
            raise ValueError("price must be non-negative")
        if multiplier <= Decimal("0"):
            raise ValueError("multiplier must be positive")
        current = self.holding(instrument_id)
        fill_time = fill_time or current.last_fill_at
        if current.quantity == Decimal("0") or _same_direction(current.quantity, signed_quantity):
            self._holdings[instrument_id] = self._increase(
                current,
                signed_quantity=signed_quantity,
                price=price,
                fill_time=fill_time,
            )
            return ()

        return self._reduce_or_flip(
            current,
            signed_quantity=signed_quantity,
            price=price,
            multiplier=multiplier,
            fill_time=fill_time,
        )

    def snapshot(self) -> Mapping[InstrumentId, Holding]:
        """Return immutable mapping of all holdings, including flat realized rows."""
        return MappingProxyType(dict(self._holdings))

    @staticmethod
    def restore(holdings: Mapping[InstrumentId, Holding]) -> HoldingBook:
        """Restore a holding book from a snapshot."""
        return HoldingBook(holdings)

    def _increase(
        self,
        current: Holding,
        *,
        signed_quantity: Decimal,
        price: Decimal,
        fill_time: datetime | None,
    ) -> Holding:
        old_abs = abs(current.quantity)
        new_quantity = current.quantity + signed_quantity
        new_abs = abs(new_quantity)
        average_cost = (
            price
            if old_abs == Decimal("0")
            else ((old_abs * current.average_cost) + (abs(signed_quantity) * price)) / new_abs
        )
        return Holding(
            instrument_id=current.instrument_id,
            quantity=new_quantity,
            average_cost=average_cost,
            realized_pnl=current.realized_pnl,
            opened_at=current.opened_at or fill_time,
            last_fill_at=fill_time,
        )

    def _reduce_or_flip(
        self,
        current: Holding,
        *,
        signed_quantity: Decimal,
        price: Decimal,
        multiplier: Decimal,
        fill_time: datetime | None,
    ) -> tuple[PositionClosed, ...]:
        close_quantity = min(abs(current.quantity), abs(signed_quantity))
        sign = Decimal("1") if current.quantity > Decimal("0") else Decimal("-1")
        close_realized = close_quantity * (price - current.average_cost) * sign * multiplier
        realized_pnl = current.realized_pnl + close_realized
        new_quantity = current.quantity + signed_quantity
        if new_quantity == Decimal("0"):
            # Reset opened_at so a subsequent re-open on the same instrument
            # records a fresh opening timestamp, not the original one from
            # before this flat-out. Without this, avg_holding_period_bars
            # accumulates across reopen cycles.
            self._holdings[current.instrument_id] = replace(
                current,
                quantity=Decimal("0"),
                realized_pnl=realized_pnl,
                opened_at=None,
                last_fill_at=fill_time,
            )
            return (
                PositionClosed(
                    instrument_id=current.instrument_id,
                    closed_quantity=close_quantity,
                    exit_price=price,
                    realized_pnl=close_realized,
                    opened_at=current.opened_at,
                    closed_at=self._close_time(fill_time),
                ),
            )
        if _same_direction(current.quantity, new_quantity):
            self._holdings[current.instrument_id] = replace(
                current,
                quantity=new_quantity,
                realized_pnl=realized_pnl,
                last_fill_at=fill_time,
            )
            return ()
        self._holdings[current.instrument_id] = Holding(
            instrument_id=current.instrument_id,
            quantity=new_quantity,
            average_cost=price,
            realized_pnl=realized_pnl,
            opened_at=fill_time,
            last_fill_at=fill_time,
        )
        return (
            PositionClosed(
                instrument_id=current.instrument_id,
                closed_quantity=abs(current.quantity),
                exit_price=price,
                realized_pnl=close_realized,
                opened_at=current.opened_at,
                closed_at=self._close_time(fill_time),
            ),
        )

    @staticmethod
    def _close_time(fill_time: datetime | None) -> datetime:
        return fill_time or datetime(1970, 1, 1, tzinfo=UTC)


def _same_direction(left: Decimal, right: Decimal) -> bool:
    return (left > Decimal("0") and right > Decimal("0")) or (
        left < Decimal("0") and right < Decimal("0")
    )


__all__ = ["CostBasisMethod", "Holding", "HoldingBook", "PositionClosed"]
