"""Holdings owned by account state, supporting average-cost and FIFO accounting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType

from qts.core.ids import InstrumentId
from qts.domain.positions import PositionSide


class CostBasisMethod(StrEnum):
    """Supported holding cost basis convention."""

    AVERAGE = "average"
    FIFO = "fifo"


@dataclass(frozen=True, slots=True)
class Lot:
    """An immutable open lot: a signed quantity acquired at a single price.

    Lots are the FIFO accounting unit. ``quantity`` carries the position side
    sign (positive for long, negative for short); ``price`` is the per-unit
    acquisition price (commission is accounted as cash movement, never in the
    lot cost). ``acquired_at`` orders lots for first-in-first-out consumption.
    """

    quantity: Decimal
    price: Decimal
    acquired_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LotConsumption:
    """Result of applying one signed fill to an ordered FIFO lot queue."""

    lots: tuple[Lot, ...]
    closed_quantity: Decimal
    realized_pnl: Decimal


class LotLedger:
    """FIFO lot accounting for a single instrument.

    Owns the rule that a reducing fill consumes the oldest open lots first and
    realizes ``consumed_qty * (exit_price - lot_price) * side_sign * multiplier``
    against each consumed lot. The ledger is a pure transformer over an ordered
    lot queue: it neither stores state nor knows about cash, so a holding book
    can drive it for either streaming fills or snapshot restore.
    """

    @staticmethod
    def average_cost(lots: tuple[Lot, ...]) -> Decimal:
        """Return the quantity-weighted average open price across lots."""
        total_quantity = sum((abs(lot.quantity) for lot in lots), Decimal("0"))
        if total_quantity == Decimal("0"):
            return Decimal("0")
        weighted = sum(
            (abs(lot.quantity) * lot.price for lot in lots),
            Decimal("0"),
        )
        return weighted / total_quantity

    @staticmethod
    def quantity(lots: tuple[Lot, ...]) -> Decimal:
        """Return the signed net quantity across lots."""
        return sum((lot.quantity for lot in lots), Decimal("0"))

    @classmethod
    def apply(
        cls,
        lots: tuple[Lot, ...],
        *,
        signed_quantity: Decimal,
        price: Decimal,
        multiplier: Decimal,
        fill_time: datetime | None,
    ) -> LotConsumption:
        """Apply one signed fill, consuming oldest lots first on a reduction.

        When the fill is flat-side or same-side as the open lots it appends a new
        lot. When it opposes the open lots it consumes them FIFO, realizing PnL,
        and any residual opens a fresh lot on the opposite side (a flip).
        """
        net = cls.quantity(lots)
        if net == Decimal("0") or PositionSide.same_for_quantities(net, signed_quantity):
            opened = (*lots, Lot(quantity=signed_quantity, price=price, acquired_at=fill_time))
            return LotConsumption(
                lots=opened,
                closed_quantity=Decimal("0"),
                realized_pnl=Decimal("0"),
            )
        return cls._reduce(
            lots,
            signed_quantity=signed_quantity,
            price=price,
            multiplier=multiplier,
            fill_time=fill_time,
        )

    @classmethod
    def _reduce(
        cls,
        lots: tuple[Lot, ...],
        *,
        signed_quantity: Decimal,
        price: Decimal,
        multiplier: Decimal,
        fill_time: datetime | None,
    ) -> LotConsumption:
        side = PositionSide.from_quantity(cls.quantity(lots))
        assert side is not None  # guaranteed: caller excludes the flat-side case
        sign = side.sign
        remaining_to_close = abs(signed_quantity)
        realized_pnl = Decimal("0")
        closed_quantity = Decimal("0")
        surviving: list[Lot] = []
        queue = list(lots)
        for index, lot in enumerate(queue):
            if remaining_to_close <= Decimal("0"):
                surviving.extend(queue[index:])
                break
            lot_abs = abs(lot.quantity)
            consumed = min(lot_abs, remaining_to_close)
            realized_pnl += consumed * (price - lot.price) * sign * multiplier
            closed_quantity += consumed
            remaining_to_close -= consumed
            if consumed < lot_abs:
                surviving.append(replace(lot, quantity=(lot_abs - consumed) * sign))
        if remaining_to_close > Decimal("0"):
            # Flip: residual opens a new lot on the opposite side.
            surviving.append(
                Lot(quantity=remaining_to_close * -sign, price=price, acquired_at=fill_time)
            )
        return LotConsumption(
            lots=tuple(surviving),
            closed_quantity=closed_quantity,
            realized_pnl=realized_pnl,
        )


@dataclass(frozen=True, slots=True)
class Holding:
    """Immutable holding snapshot.

    Commission is accounted as cash movement, not as part of cost basis. Under
    ``CostBasisMethod.AVERAGE`` realized PnL marks reductions against
    ``average_cost`` and ``lots`` is empty. Under ``CostBasisMethod.FIFO`` the
    open ``lots`` are the source of truth; ``average_cost`` is the
    quantity-weighted average of the open lots, kept consistent so valuation and
    unrealized PnL behave identically across methods.
    """

    instrument_id: InstrumentId
    quantity: Decimal
    average_cost: Decimal
    realized_pnl: Decimal
    cost_basis_method: CostBasisMethod = CostBasisMethod.AVERAGE
    opened_at: datetime | None = None
    last_fill_at: datetime | None = None
    lots: tuple[Lot, ...] = field(default_factory=tuple)

    def market_value(self, mark_price: Decimal, multiplier: Decimal) -> Decimal:
        """Return signed market value at the supplied mark."""
        return self.quantity * mark_price * multiplier

    def unrealized_pnl(self, mark_price: Decimal, multiplier: Decimal) -> Decimal:
        """Return unrealized PnL at the supplied mark."""
        side = PositionSide.from_quantity(self.quantity)
        if side is None:
            return Decimal("0")
        return abs(self.quantity) * (mark_price - self.average_cost) * side.sign * multiplier

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
    """Mutable holding book supporting average-cost and FIFO accounting.

    The cost basis convention is per holding: ``apply_fill`` reads the existing
    holding's ``cost_basis_method`` (defaulting to AVERAGE for a fresh holding)
    so average-cost behavior is unchanged while FIFO holdings consume their
    oldest lots first on a reduction.
    """

    def __init__(
        self,
        holdings: Mapping[InstrumentId, Holding] | None = None,
        *,
        cost_basis_method: CostBasisMethod = CostBasisMethod.AVERAGE,
    ) -> None:
        self._holdings: dict[InstrumentId, Holding] = dict(holdings or {})
        self._cost_basis_method = cost_basis_method

    def holding(self, instrument_id: InstrumentId) -> Holding:
        """Return the current holding or a flat zero-cost snapshot."""
        return self._holdings.get(
            instrument_id,
            Holding(
                instrument_id=instrument_id,
                quantity=Decimal("0"),
                average_cost=Decimal("0"),
                realized_pnl=Decimal("0"),
                cost_basis_method=self._cost_basis_method,
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
        if current.cost_basis_method is CostBasisMethod.FIFO:
            return self._apply_fill_fifo(
                current,
                signed_quantity=signed_quantity,
                price=price,
                multiplier=multiplier,
                fill_time=fill_time,
            )
        if current.quantity == Decimal("0") or PositionSide.same_for_quantities(
            current.quantity,
            signed_quantity,
        ):
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
            cost_basis_method=current.cost_basis_method,
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
        if PositionSide.same_for_quantities(current.quantity, new_quantity):
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
            cost_basis_method=current.cost_basis_method,
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

    def _apply_fill_fifo(
        self,
        current: Holding,
        *,
        signed_quantity: Decimal,
        price: Decimal,
        multiplier: Decimal,
        fill_time: datetime | None,
    ) -> tuple[PositionClosed, ...]:
        consumption = LotLedger.apply(
            current.lots,
            signed_quantity=signed_quantity,
            price=price,
            multiplier=multiplier,
            fill_time=fill_time,
        )
        new_quantity = LotLedger.quantity(consumption.lots)
        realized_pnl = current.realized_pnl + consumption.realized_pnl
        flipped = (
            current.quantity != Decimal("0")
            and new_quantity != Decimal("0")
            and not PositionSide.same_for_quantities(current.quantity, new_quantity)
        )
        opened_at = self._fifo_opened_at(
            current,
            new_quantity=new_quantity,
            flipped=flipped,
            fill_time=fill_time,
        )
        self._holdings[current.instrument_id] = Holding(
            instrument_id=current.instrument_id,
            quantity=new_quantity,
            average_cost=LotLedger.average_cost(consumption.lots),
            realized_pnl=realized_pnl,
            cost_basis_method=CostBasisMethod.FIFO,
            opened_at=opened_at,
            last_fill_at=fill_time,
            lots=consumption.lots,
        )
        # Match the average-cost contract: a PositionClosed event fires only when
        # the holding reaches flat or flips side, not on a partial reduction that
        # leaves the position open on the same side. FIFO differs from average
        # cost only in the realized-PnL figure, never in emission semantics.
        if not (new_quantity == Decimal("0") or flipped):
            return ()
        return (
            PositionClosed(
                instrument_id=current.instrument_id,
                closed_quantity=consumption.closed_quantity,
                exit_price=price,
                realized_pnl=consumption.realized_pnl,
                opened_at=current.opened_at,
                closed_at=self._close_time(fill_time),
            ),
        )

    @staticmethod
    def _fifo_opened_at(
        current: Holding,
        *,
        new_quantity: Decimal,
        flipped: bool,
        fill_time: datetime | None,
    ) -> datetime | None:
        if new_quantity == Decimal("0"):
            # Flat-out: reset so a re-open records a fresh opening timestamp.
            return None
        if current.quantity == Decimal("0") or flipped:
            return fill_time
        return current.opened_at or fill_time

    @staticmethod
    def _close_time(fill_time: datetime | None) -> datetime:
        return fill_time or datetime(1970, 1, 1, tzinfo=UTC)


__all__ = [
    "CostBasisMethod",
    "Holding",
    "HoldingBook",
    "Lot",
    "LotConsumption",
    "LotLedger",
    "PositionClosed",
]
