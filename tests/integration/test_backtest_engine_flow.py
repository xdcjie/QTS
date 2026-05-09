from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.domain.market_data import Bar


def _bar(start: datetime, close: str) -> Bar:
    from qts.core.ids import InstrumentId

    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_backtest_engine_runs_strategy_through_execution_flow() -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import Strategy

    class BuyOnceStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.has_ordered = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            assert ctx.data.close(self.asset) == bar.close
            if not self.has_ordered:
                ctx.target_quantity(self.asset, Decimal("10"))
                self.has_ordered = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")],
        initial_cash=Decimal("10000"),
    ).run()

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert result.final_account.positions[instrument_id].quantity == Decimal("10")
    assert result.final_account.cash["USD"] == Decimal("9000")
    assert result.orders[0].state.value == "filled"
    assert result.processed_bars == 2


def test_backtest_engine_target_intents_must_pass_pre_trade_risk_before_order_manager() -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.strategy_sdk import Strategy

    class OversizedOrderStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("10"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine(
        strategy=OversizedOrderStrategy(),
        bars=[_bar(start, "100")],
        initial_cash=Decimal("10000"),
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("999"))]),
    ).run()

    assert result.orders == ()
    assert result.final_account.cash["USD"] == Decimal("10000")
    assert result.final_account.positions == {}
