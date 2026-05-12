from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


def _bar(start: datetime, close: str = "100") -> Bar:
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


def test_backtest_actor_loop_processes_bars_and_returns_runtime_result(tmp_path: Path) -> None:
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
    from qts.backtest.engine import BacktestCostModel, _BacktestExecutionAdapter
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.backtest.intent_processor import BacktestIntentProcessor
    from qts.backtest.portfolio_projection import BacktestPortfolioProjector
    from qts.backtest.report import StreamingBacktestArtifactWriter
    from qts.backtest.sinks import BacktestStreamingSink
    from qts.core.ids import InstrumentId
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule

    class OneOrderStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.placed = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if not self.placed:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.placed = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")]
    strategy = OneOrderStrategy()
    instrument_context = BacktestInstrumentContext(
        instrument_registry=None,
        registry_bars=bars,
    )
    portfolio_projector = BacktestPortfolioProjector()
    intent_processor = BacktestIntentProcessor(
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("1000000"))]),
        instrument_context=instrument_context,
        multiplier_for=portfolio_projector.multiplier_for,
    )

    loop = BacktestActorLoop(
        strategy=strategy,
        bars=bars,
        config=BacktestActorLoopConfig(initial_cash=Decimal("10000"), warmup_bars=0),
        dependencies=BacktestActorLoopDependencies(
            instrument_registry=instrument_context.instrument_registry(),
            contract_multipliers={},
            execution_adapter=_BacktestExecutionAdapter(BacktestCostModel()),
            process_intent=intent_processor.process_intent,
            portfolio_view=portfolio_projector.portfolio_view,
            equity_point=portfolio_projector.equity_point,
            update_rolling_prices=instrument_context.update_rolling_prices,
        ),
    )
    writer = StreamingBacktestArtifactWriter(tmp_path)
    sink = BacktestStreamingSink(writer)
    runtime = loop.run(sink=sink, prune_history=True, compact_orders=True)

    writer.finalize(
        config_hash="cfg",
        dataset_metadata=(),
        cost_model={},
        processed_bars=runtime.processed_bars,
        warmup_bars=runtime.warmup_bars,
        trading_bars=runtime.trading_bars,
        final_cash=runtime.final_account.cash["USD"],
        strategy_version="test",
    )

    assert runtime.processed_bars == 2
    assert runtime.trading_bars == 2
    assert runtime.warmup_bars == 0
    assert runtime.final_account.positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    assert sink.order_count == 1
