"""Risk state snapshot: pre-computed account/risk state for OrderRiskRequest population."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from qts.core.ids import InstrumentId
from qts.portfolio.account_snapshot import AccountSnapshot
from qts.portfolio.valuation.valuator import PortfolioValuator

if TYPE_CHECKING:
    from qts.risk.margin.calculator import MarginCalculator


@dataclass(frozen=True, slots=True)
class RiskStateSnapshot:
    """Immutable risk-relevant state derived from account snapshot and market prices.

    This is the single source of risk context for OrderRiskRequest construction.
    If any field required by an enabled risk rule is missing, the risk check must
    fail closed (reject the order), NOT silently pass.
    """

    account_equity: Decimal
    current_exposure: Decimal
    current_notional_by_instrument: Mapping[InstrumentId, Decimal]
    current_position_by_instrument: Mapping[InstrumentId, Decimal]
    intraday_pnl: Decimal
    current_margin_requirement: Decimal
    available_margin: Decimal

    @classmethod
    def from_account(
        cls,
        snapshot: AccountSnapshot,
        *,
        marks: Mapping[InstrumentId, Decimal],
        multipliers: Mapping[InstrumentId, Decimal],
        intraday_pnl: Decimal = Decimal("0"),
        current_margin_requirement: Decimal = Decimal("0"),
        available_margin: Decimal = Decimal("0"),
        margin_calculator: MarginCalculator | None = None,
    ) -> RiskStateSnapshot:
        """Build risk state from an account snapshot and current mark prices.

        Raises ValueError if account_equity would be zero or negative, because
        risk rules that depend on equity cannot function without it.

        When margin_calculator is supplied, initial and maintenance margin
        requirements are computed from positions, marks, multipliers, and
        account_equity; the explicit current_margin_requirement and
        available_margin parameters are ignored.
        """
        valuation = PortfolioValuator.valuate(
            cash=snapshot.cash,
            holdings=snapshot.holdings,
            marks=marks,
            multipliers=multipliers,
        )
        if margin_calculator is not None:
            margin_req = margin_calculator.margin_requirement(
                positions=snapshot.holdings,
                marks=marks,
                multipliers=multipliers,
                account_equity=valuation.account_equity,
            )
            current_margin_requirement = margin_req.initial_margin
            available_margin = margin_req.available_margin
        return cls(
            account_equity=valuation.account_equity,
            current_exposure=valuation.current_exposure,
            current_notional_by_instrument=valuation.current_notional_by_instrument,
            current_position_by_instrument=valuation.current_position_by_instrument,
            intraday_pnl=intraday_pnl,
            current_margin_requirement=current_margin_requirement,
            available_margin=available_margin,
        )

    def current_position(self, instrument_id: InstrumentId) -> Decimal:
        """Return the current position for an instrument, defaulting to zero."""
        return self.current_position_by_instrument.get(instrument_id, Decimal("0"))


__all__ = ["RiskStateSnapshot"]
