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
        fx_rates: Mapping[str, Decimal] | None = None,
        base_currency: str = "USD",
    ) -> AccountValuation:
        """Return a full account valuation in ``base_currency``.

        Each holding's market value = quantity * mark_price * multiplier.
        Cash is converted to the base currency using ``fx_rates`` (base units
        per 1 unit of the currency). When ``fx_rates`` is None all cash is
        assumed base-denominated (single-currency account). When ``fx_rates`` is
        supplied, a non-base currency with no rate raises (fail closed) rather
        than silently summing mixed currencies.
        account_equity = converted cash + sum(holding market values).
        current_exposure = sum(abs(holding market values)).
        """
        total_cash = PortfolioValuator._convert_cash(
            cash=cash, fx_rates=fx_rates, base_currency=base_currency
        )
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

    @staticmethod
    def _convert_cash(
        *,
        cash: Mapping[str, Decimal],
        fx_rates: Mapping[str, Decimal] | None,
        base_currency: str,
    ) -> Decimal:
        """Convert all cash balances into the base currency.

        ``fx_rates`` maps a currency to base units per 1 unit of that currency.
        Missing a non-base currency rate (when fx_rates is supplied) fails closed.
        """
        base = base_currency.strip().upper()
        normalized_rates = (
            {currency.strip().upper(): rate for currency, rate in fx_rates.items()}
            if fx_rates is not None
            else None
        )
        total = Decimal("0")
        for currency, balance in cash.items():
            ccy = currency.strip().upper()
            if ccy == base:
                rate = Decimal("1")
            elif normalized_rates is None:
                rate = Decimal("1")
            else:
                try:
                    rate = normalized_rates[ccy]
                except KeyError:
                    raise ValueError(
                        f"missing FX rate for currency {ccy} to value account in {base}"
                    ) from None
            total += balance * rate
        return total


__all__ = ["AccountValuation", "PortfolioValuator"]
