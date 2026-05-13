"""Portfolio projection helpers for backtest runtime."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.reporting.backtest import EquityCurvePoint
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.strategy_sdk import PortfolioPosition, PortfolioView


class BacktestPortfolioProjector:
    """Compute portfolio state views and equity points for streaming backtests."""

    def __init__(self, contract_multipliers: Mapping[InstrumentId, Decimal] | None = None) -> None:
        """Perform __init__."""
        self._multipliers: dict[InstrumentId, Decimal] = dict(contract_multipliers or {})

    def multiplier_for(self, instrument_id: InstrumentId) -> Decimal:
        """Return multiplier used for portfolio valuation and risk checks."""

        return self._multipliers.get(instrument_id, Decimal("1"))

    def portfolio_view(
        self,
        snapshot: AccountSnapshot,
        latest_prices: Mapping[InstrumentId, Decimal],
    ) -> PortfolioView:
        """Perform portfolio_view."""
        positions = {
            instrument_id: PortfolioPosition(
                quantity=position.quantity,
                market_value=(
                    position.quantity
                    * latest_prices.get(instrument_id, Decimal("0"))
                    * self.multiplier_for(instrument_id)
                ),
            )
            for instrument_id, position in snapshot.positions.items()
        }
        cash = snapshot.cash["USD"]
        equity = cash + sum(
            (position.market_value for position in positions.values()),
            Decimal("0"),
        )
        return PortfolioView(cash=cash, equity=equity, positions=positions)

    def equity_point(
        self,
        bar: Bar,
        snapshot: AccountSnapshot,
        latest_prices: Mapping[InstrumentId, Decimal],
    ) -> EquityCurvePoint:
        """Perform equity_point."""
        return EquityCurvePoint(
            time=bar.end_time,
            equity=self.portfolio_view(snapshot, latest_prices=latest_prices).equity,
        )


__all__ = ["BacktestPortfolioProjector"]
