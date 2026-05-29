"""Portfolio valuation: compute account equity, exposure, and position-level notional."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding


@dataclass(frozen=True, slots=True)
class AccountValuation:
    """Marked-to-market portfolio valuation derived from account snapshot and prices."""

    account_equity: Decimal
    current_exposure: Decimal
    current_notional_by_instrument: Mapping[InstrumentId, Decimal]
    current_position_by_instrument: Mapping[InstrumentId, Decimal]


class PortfolioValuator:
    """Compute account-level valuation from holdings, cash, mark prices, and multipliers."""

    @staticmethod
    def valuate(
        *,
        cash: Mapping[str, Decimal],
        holdings: Mapping[InstrumentId, Holding],
        marks: Mapping[InstrumentId, Decimal],
        multipliers: Mapping[InstrumentId, Decimal],
    ) -> AccountValuation:
        """Return a full account valuation.

        Each holding's market value = quantity * mark_price * multiplier.
        account_equity = sum(cash balances) + sum(holding market values).
        current_exposure = sum(abs(holding market values)).
        """
        total_cash = sum(cash.values(), Decimal("0"))
        holding_equity = Decimal("0")
        exposure = Decimal("0")
        notional_by_instrument: dict[InstrumentId, Decimal] = {}
        position_by_instrument: dict[InstrumentId, Decimal] = {}

        for instrument_id, holding in holdings.items():
            mark = marks.get(instrument_id)
            multiplier = multipliers.get(instrument_id, Decimal("1"))
            market_value = Decimal("0")
            if mark is not None and holding.quantity != Decimal("0"):
                market_value = holding.quantity * mark * multiplier
            holding_equity += market_value
            exposure += abs(market_value)
            notional_by_instrument[instrument_id] = abs(market_value)
            position_by_instrument[instrument_id] = holding.quantity

        account_equity = total_cash + holding_equity

        return AccountValuation(
            account_equity=account_equity,
            current_exposure=exposure,
            current_notional_by_instrument=notional_by_instrument,
            current_position_by_instrument=position_by_instrument,
        )


__all__ = ["AccountValuation", "PortfolioValuator"]
