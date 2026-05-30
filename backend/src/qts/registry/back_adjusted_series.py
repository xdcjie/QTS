"""Back-adjusted continuous futures price series from roll history."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.registry.future_roll import FutureRollRegistry


@dataclass(frozen=True, slots=True)
class RollAdjustmentPoint:
    """One roll boundary with proportional adjustment factor."""

    as_of: datetime
    old_contract: InstrumentId
    new_contract: InstrumentId
    old_price: Decimal
    new_price: Decimal
    adjustment_factor: Decimal

    def __post_init__(self) -> None:
        if self.adjustment_factor <= Decimal("0"):
            raise ValueError("adjustment_factor must be positive")


class BackAdjustedContinuousSeriesBuilder:
    """Build back-adjusted continuous futures price series from roll history.

    Proportional (ratio-based) back-adjustment ensures no artificial price
    jump at roll boundaries.  At each roll the *adjustment_factor* is
    ``old_price / new_price``.  To convert a raw pre-roll price into a
    back-adjusted price, divide by the cumulative product of all adjustment
    factors from rolls that occurred *after* the raw price timestamp.
    """

    def __init__(self, *, future_roll_registry: FutureRollRegistry) -> None:
        self._registry = future_roll_registry

    def build_adjustment_factors(
        self, continuous_id: InstrumentId
    ) -> tuple[RollAdjustmentPoint, ...]:
        """Compute adjustment factors at each roll boundary.

        Iterates the selection history for *continuous_id*, detects
        contract-switch points, and computes proportional adjustment
        factors using the prices recorded in each selection.
        """
        front_id = self._registry.front_continuous_id(continuous_id)
        selections = self._registry.selection_history(front_id)
        if len(selections) < 2:
            return ()

        points: list[RollAdjustmentPoint] = []
        prev_contract = selections[0].concrete_instrument_id
        for selection in selections[1:]:
            current_contract = selection.concrete_instrument_id
            if current_contract != prev_contract:
                prev_selection = self._registry.selection_at(front_id, as_of=selection.as_of)
                old_price = prev_selection.prices_by_instrument.get(prev_contract)
                new_price = prev_selection.prices_by_instrument.get(current_contract)
                if old_price is not None and new_price is not None and new_price != Decimal("0"):
                    factor = old_price / new_price
                    points.append(
                        RollAdjustmentPoint(
                            as_of=selection.as_of,
                            old_contract=prev_contract,
                            new_contract=current_contract,
                            old_price=old_price,
                            new_price=new_price,
                            adjustment_factor=factor,
                        )
                    )
                prev_contract = current_contract
        return tuple(points)

    def adjusted_price(
        self,
        *,
        raw_price: Decimal,
        as_of: datetime,
        continuous_id: InstrumentId,
    ) -> Decimal:
        """Apply cumulative adjustment factor to a raw price.

        Divides *raw_price* by the product of all adjustment factors from
        rolls that occurred *after* *as_of*.  This produces a
        back-adjusted price that is continuous with the most recent
        contract's raw prices.
        """
        front_id = self._registry.front_continuous_id(continuous_id)
        adjustments = self.build_adjustment_factors(front_id)
        cumulative = Decimal("1")
        for point in adjustments:
            if point.as_of > as_of:
                cumulative *= point.adjustment_factor
        if cumulative == Decimal("0"):
            raise ValueError("cumulative adjustment factor is zero; cannot adjust price")
        return raw_price / cumulative

    def series_hash(self, continuous_id: InstrumentId) -> str:
        """Return a deterministic sha256 over the roll adjustment points.

        Provides reproducibility evidence for a back-adjusted series: the same
        roll history (boundaries, raw prices, factors) yields the same hash, so
        a recorded adjusted series can be verified against the roll registry.
        """
        adjustments = self.build_adjustment_factors(continuous_id)
        digest = hashlib.sha256()
        for point in adjustments:
            digest.update(
                "|".join(
                    (
                        point.as_of.isoformat(),
                        str(point.old_contract),
                        str(point.new_contract),
                        str(point.old_price),
                        str(point.new_price),
                        str(point.adjustment_factor),
                    )
                ).encode("utf-8")
            )
            digest.update(b"\n")
        return f"sha256:{digest.hexdigest()}"


__all__ = ["BackAdjustedContinuousSeriesBuilder", "RollAdjustmentPoint"]
