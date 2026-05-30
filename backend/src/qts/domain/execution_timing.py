"""Fill-timing domain model and fill-policy selection.

Domain rule
-----------
A trading decision is made at the close of a *completed* bar N (the strategy
only sees bar N once it has finished). The earliest price that decision can be
acted on is the open of the next bar, N+1. Filling at bar N's own close is
look-ahead: the close is unknowable while the bar is still forming, so a
backtest that fills there is optimistic and cannot, on its own, back
paper/live promotion evidence.

This module is the shared domain owner of that rule so backtest, runtime/config,
and research can agree on fill-timing semantics without runtime importing the
backtest layer or research importing the execution layer. ``ExecutionTimingModel``
selects a ``FillPolicy`` and answers "which price realizes a decision at bar N":

* ``NEXT_BAR_OPEN`` (promotion-grade default): the loop defers the accepted
  intent to the next strategy-facing bar for the instrument and fills at that
  bar's ``open``.
* ``SAME_BAR_CLOSE`` (research-only): fills at the decision bar's ``close``.
  This is optimistic look-ahead, requires an explicit optimistic waiver to be
  used at all, and is never promotion-grade evidence.

The model is injected into ``BacktestInstrumentContext`` (the single point
where the normal-instrument execution price is decided) so the same intent
path -- Strategy SDK -> Risk -> OrderManager -> Execution -> Account -- is
preserved for every policy; only the price source and the bar it is taken from
change.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from qts.domain.market_data import Bar


class FillPolicy(Enum):
    """Fill-timing policy for a decision made at a completed bar."""

    SAME_BAR_CLOSE = "same_bar_close"
    NEXT_BAR_OPEN = "next_bar_open"

    @classmethod
    def from_value(cls, value: str) -> FillPolicy:
        """Resolve a policy from its serialized config value."""
        normalized = value.strip().lower()
        for policy in cls:
            if policy.value == normalized:
                return policy
        supported = ", ".join(policy.value for policy in cls)
        raise ValueError(f"unsupported fill_policy: {value!r} (supported: {supported})")


@dataclass(frozen=True, slots=True)
class ExecutionTimingModel:
    """Own fill-policy selection and the price that realizes a decision.

    The construction default is ``next_bar_open`` (promotion-grade
    next-obtainable execution). ``same_bar_close`` is optimistic look-ahead: it
    may only be constructed with an explicit ``optimistic_waiver`` and is never
    promotion-grade evidence, even with the waiver. The waiver records an
    informed research decision to accept the optimistic fill; it does not make
    the result eligible to feed paper/live promotion.
    """

    fill_policy: FillPolicy = FillPolicy.NEXT_BAR_OPEN
    optimistic_waiver: bool = False

    def __post_init__(self) -> None:
        """Reject optimistic same-bar fills without an explicit waiver."""
        if self.fill_policy is FillPolicy.SAME_BAR_CLOSE and not self.optimistic_waiver:
            raise ValueError(
                "same_bar_close is optimistic look-ahead and requires "
                "optimistic_waiver=True to be used"
            )

    @classmethod
    def promotion_grade(cls) -> ExecutionTimingModel:
        """Return the promotion-grade default model (``next_bar_open``)."""
        return cls(fill_policy=FillPolicy.NEXT_BAR_OPEN)

    @classmethod
    def research_only(cls, *, optimistic_waiver: bool = True) -> ExecutionTimingModel:
        """Return the research-only ``same_bar_close`` model.

        ``optimistic_waiver`` records the explicit decision to accept the
        optimistic same-bar fill for research; it defaults to ``True`` because
        constructing ``same_bar_close`` without the waiver is rejected. The
        resulting model is never promotion-grade.
        """
        return cls(
            fill_policy=FillPolicy.SAME_BAR_CLOSE,
            optimistic_waiver=optimistic_waiver,
        )

    @classmethod
    def from_value(cls, value: str, *, optimistic_waiver: bool = False) -> ExecutionTimingModel:
        """Build a model from a serialized ``fill_policy`` config value."""
        return cls(
            fill_policy=FillPolicy.from_value(value),
            optimistic_waiver=optimistic_waiver,
        )

    @property
    def defers_to_next_bar(self) -> bool:
        """Return whether an accepted intent fills on the next bar, not this one."""
        return self.fill_policy is FillPolicy.NEXT_BAR_OPEN

    @property
    def is_optimistic(self) -> bool:
        """Return whether this policy fills at an unobtainable same-bar price."""
        return self.fill_policy is FillPolicy.SAME_BAR_CLOSE

    @property
    def is_promotion_grade(self) -> bool:
        """Return whether fills under this model may back promotion evidence.

        ``next_bar_open`` is always promotion-grade. ``same_bar_close`` is never
        promotion-grade: the optimistic look-ahead it introduces disqualifies it
        from paper/live readiness evidence regardless of any research waiver.
        """
        return self.fill_policy is FillPolicy.NEXT_BAR_OPEN

    def price_for_execution_bar(self, bar: Bar) -> Decimal:
        """Return the fill price for the bar an intent executes against.

        For ``same_bar_close`` the execution bar is the decision bar and the
        price is its ``close``. For ``next_bar_open`` the loop passes the next
        bar and the price is that bar's ``open``.
        """
        if self.fill_policy is FillPolicy.NEXT_BAR_OPEN:
            return bar.open
        return bar.close

    def to_manifest_payload(self) -> dict[str, object]:
        """Serialize the fill-timing assumptions for the backtest manifest."""
        return {
            "fill_policy": self.fill_policy.value,
            "fill_timing_basis": ("next_bar_open" if self.defers_to_next_bar else "same_bar_close"),
            "optimistic": self.is_optimistic,
            "optimistic_waiver": self.optimistic_waiver,
            "promotion_grade": self.is_promotion_grade,
        }


__all__ = ["ExecutionTimingModel", "FillPolicy"]
