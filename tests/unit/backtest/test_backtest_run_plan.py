from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.backtest.run_plan import BacktestRunPlan
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


class _NoopStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: object) -> None:
        return None


def _bar() -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_backtest_engine_consumes_backtest_run_plan() -> None:
    strategy = _NoopStrategy()
    plan = BacktestRunPlan.from_inputs(
        strategy=strategy,
        bars=[_bar()],
        initial_cash=Decimal("10000"),
    )

    engine = BacktestEngine.from_run_plan(plan)

    assert engine._strategies == (strategy,)
    assert engine._config is plan.engine_config
    assert engine._risk_engine is plan.dependencies.risk_engine
    assert engine._registry_bars == plan.registry_bars


def test_backtest_engine_constructor_surface_is_plan_first() -> None:
    parameters = inspect.signature(BacktestEngine).parameters

    assert tuple(parameters) == ("plan",)
