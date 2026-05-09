from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any


def test_example_strategy_runs_through_paper_like_backtest_runtime() -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar
    from qts.strategy_sdk import Strategy

    class BuyOnce(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.done = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if not self.done:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.done = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bar = Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        is_complete=True,
    )

    result = BacktestEngine(
        strategy=BuyOnce(),
        bars=[bar],
        initial_cash=Decimal("1000"),
    ).run()

    assert result.final_account.positions[InstrumentId("EQUITY.US.NASDAQ.AAPL")].quantity == 1
    assert result.orders[0].state.value == "filled"
