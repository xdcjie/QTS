from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.backtest.portfolio_projection import BacktestPortfolioProjector
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.portfolio.holdings import Holding
from qts.runtime.actors.account_actor import AccountSnapshot


def _snapshot_with_position() -> tuple[AccountSnapshot, InstrumentId]:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    return (
        AccountSnapshot(
            cash={"USD": Decimal("10000")},
            positions={
                instrument_id: Holding(
                    instrument_id=instrument_id,
                    quantity=Decimal("2"),
                    average_cost=Decimal("0"),
                    realized_pnl=Decimal("0"),
                ),
            },
        ),
        instrument_id,
    )


def _bar(time: datetime, close: str) -> Bar:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    return Bar(
        instrument_id=instrument_id,
        start_time=time,
        end_time=time + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_portfolio_projector_applies_multipliers_and_sums_equity() -> None:
    snapshot, instrument_id = _snapshot_with_position()
    projector = BacktestPortfolioProjector({instrument_id: Decimal("5")})

    view = projector.portfolio_view(
        snapshot,
        latest_prices={instrument_id: Decimal("3")},
    )

    assert view.cash == Decimal("10000")
    assert view.positions[instrument_id].market_value == Decimal("30")
    assert view.equity == Decimal("10030")


def test_portfolio_projector_builds_equity_point() -> None:
    snapshot, instrument_id = _snapshot_with_position()
    projector = BacktestPortfolioProjector({instrument_id: Decimal("2")})
    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "10")

    point = projector.equity_point(
        bar,
        snapshot,
        latest_prices={instrument_id: Decimal("10")},
    )

    assert point.time == bar.end_time
    assert point.equity == Decimal("10040")
