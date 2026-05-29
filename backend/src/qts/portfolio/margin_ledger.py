"""Stateful margin ledger owned by the portfolio layer.

The :class:`MarginLedger` tracks the three margin quantities a futures account
carries through its lifecycle:

* ``initial_margin`` -- collateral required to open the current positions.
* ``maintenance_margin`` -- the floor below which a margin call is triggered.
* ``variation_margin`` -- the cumulative mark-to-market profit or loss settled
  against the account as marks move.

Initial and maintenance margin are *requirements* derived from current notional
via the rate-based :class:`~qts.risk.margin.calculator.MarginCalculator`. They
depend only on the present position and mark, not on history, so the ledger
recomputes them on every update.

Variation margin is *path-dependent*: it accumulates the realized + unrealized
mark-to-market deltas as the mark moves, exactly as a clearing house debits or
credits an account daily. It is tracked separately from the rate-based
requirement and is the ledger's only piece of mutable, history-carrying state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding
from qts.risk.margin.calculator import MarginCalculator


@dataclass(frozen=True, slots=True)
class MarginState:
    """Immutable snapshot of the margin ledger at a point in time."""

    initial_margin: Decimal
    maintenance_margin: Decimal
    variation_margin: Decimal


class MarginLedger:
    """Mutable margin ledger tracking initial, maintenance, and variation margin.

    The ledger consumes a :class:`MarginCalculator` for the rate-based initial
    and maintenance requirements and accumulates variation margin as the mark
    moves. ``update`` is called whenever positions or marks change; it returns
    the resulting :class:`MarginState`.
    """

    def __init__(
        self,
        *,
        calculator: MarginCalculator | None = None,
        account_equity: Decimal = Decimal("0"),
    ) -> None:
        self._calculator = calculator or MarginCalculator()
        self._account_equity = account_equity
        self._variation_margin = Decimal("0")
        self._last_marks: dict[InstrumentId, Decimal] = {}
        self._initial_margin = Decimal("0")
        self._maintenance_margin = Decimal("0")

    def update(
        self,
        positions: Mapping[InstrumentId, Holding],
        marks: Mapping[InstrumentId, Decimal],
        multipliers: Mapping[InstrumentId, Decimal],
    ) -> MarginState:
        """Recompute requirements and accrue variation margin from mark moves.

        Variation margin for each held instrument accrues ``signed_quantity *
        (new_mark - prior_mark) * multiplier`` -- the mark-to-market settlement
        a clearing house would apply between two marks. The first mark seen for
        an instrument seeds the reference and accrues nothing.
        """
        for instrument_id, holding in positions.items():
            mark = marks.get(instrument_id)
            if mark is None or holding.quantity == Decimal("0"):
                continue
            prior_mark = self._last_marks.get(instrument_id)
            if prior_mark is not None:
                multiplier = multipliers.get(instrument_id, Decimal("1"))
                self._variation_margin += holding.quantity * (mark - prior_mark) * multiplier
            self._last_marks[instrument_id] = mark

        requirement = self._calculator.margin_requirement(
            positions=positions,
            marks=marks,
            multipliers=multipliers,
            account_equity=self._account_equity,
        )
        self._initial_margin = requirement.initial_margin
        self._maintenance_margin = requirement.maintenance_margin
        return self.state()

    def state(self) -> MarginState:
        """Return the current margin state snapshot."""
        return MarginState(
            initial_margin=self._initial_margin,
            maintenance_margin=self._maintenance_margin,
            variation_margin=self._variation_margin,
        )

    @property
    def variation_margin(self) -> Decimal:
        """Return the accumulated variation margin."""
        return self._variation_margin


__all__ = ["MarginLedger", "MarginState"]
