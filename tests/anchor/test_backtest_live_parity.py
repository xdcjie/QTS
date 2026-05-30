from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)
from qts.strategy_sdk import Strategy

from tests.support.backtest_streaming import run_engine_streaming

_PARITY_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


class _BuyOnFirstBar(Strategy):
    """Target a 10-lot long on the first bar, then hold."""

    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self._placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self._placed:
            ctx.target_quantity(self.asset, Decimal("10"))
            self._placed = True


def _flat_bars() -> list[Bar]:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return [
        Bar(
            instrument_id=_PARITY_INSTRUMENT,
            start_time=start + timedelta(minutes=index),
            end_time=start + timedelta(minutes=index + 1),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("100"),
            high=Decimal("100"),
            low=Decimal("100"),
            close=Decimal("100"),
            volume=Decimal("100"),
            is_complete=True,
        )
        for index in range(2)
    ]


def _parity_config(*, max_notional: str) -> BacktestRuntimeConfig:
    return BacktestRuntimeConfig(
        roots=("AAPL",),
        symbols=("AAPL",),
        start=datetime(2026, 1, 2, tzinfo=UTC),
        end=datetime(2026, 1, 3, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("100000"),
        strategy_class="tests.anchor.parity.BuyOnFirstBar",
        market_data=BacktestMarketDataReference(config_path=Path("md.yaml"), catalog="research"),
        instrument_ids={"AAPL": _PARITY_INSTRUMENT},
        risk_config=BacktestRiskConfig(max_notional=Decimal(max_notional)),
    )


def test_backtest_live_parity_document_is_required_by_agents() -> None:
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    required_docs = agents.split("## Architecture rules", maxsplit=1)[0]

    assert "`docs/architecture/backtest_live_parity.md`" in required_docs


def test_backtest_live_parity_document_renders_core_flow_as_mermaid() -> None:
    doc = Path("docs/architecture/backtest_live_parity.md").read_text(encoding="utf-8")

    assert "```mermaid" in doc
    assert 'Strategy["Strategy SDK"] --> Context["StrategyContext"]' in doc
    assert 'Account["AccountActor"] --> Portfolio' in doc


def test_backtest_engine_order_path_uses_shared_actor_chain() -> None:
    from qts.backtest import engine
    from qts.backtest.engine_assembly import BacktestEngineAssembler

    engine_source = inspect.getsource(engine.BacktestEngine)
    run_source = inspect.getsource(engine.BacktestEngine.run_streaming)
    # QTS-FINAL-002 moved collaborator construction (incl. SimulatedExecutionAdapter)
    # into BacktestEngineAssembler; it is still part of the shared backtest order path.
    engine_assembly_source = inspect.getsource(BacktestEngineAssembler)
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.runtime.actors.order_manager_actor import OrderManagerActor
    from qts.runtime.execution_report_handler import ExecutionReportHandler
    from qts.runtime.intent_processing import OrderPlanBuilder, TargetIntentProcessor
    from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline

    actor_loop_source = inspect.getsource(BacktestActorLoop)
    order_manager_actor_source = inspect.getsource(OrderManagerActor)
    order_plan_builder_source = inspect.getsource(OrderPlanBuilder)
    processor_source = inspect.getsource(TargetIntentProcessor)
    report_handler_source = inspect.getsource(ExecutionReportHandler)
    strategy_pipeline_source = inspect.getsource(StrategyExecutionPipeline)

    assert "BacktestActorLoop" in run_source

    for required in (
        "AccountActor",
        "OrderManagerActor",
        "ExecutionActor",
        "SimulatedExecutionAdapter",
    ):
        assert (
            required in actor_loop_source
            or required in engine_source
            or required in engine_assembly_source
        )
    assert "StrategyContext" in strategy_pipeline_source
    assert "StrategyActor" in strategy_pipeline_source
    assert "SignalAggregatorActor" in strategy_pipeline_source
    assert "OrderRiskRequest" in processor_source
    assert ".check(" in processor_source or ".check" in processor_source
    assert "SubmitOrder" in processor_source
    assert "OrderPlanBuilder" in processor_source
    assert "order_instrument_for_intent" in order_plan_builder_source
    assert "market_price_for_intent" in order_plan_builder_source
    assert "ExecutionReportHandler" in order_manager_actor_source
    assert "ApplyFill" in order_manager_actor_source
    assert "ApplyFill" not in report_handler_source
    assert "ApplyFill" not in engine_source


def test_live_runtime_session_uses_shared_actor_chain() -> None:
    import qts.runtime.broker_runtime_topology as broker_runtime_topology
    import qts.runtime.dependencies as runtime_dependencies
    import qts.runtime.session as runtime_session

    source = (
        inspect.getsource(runtime_dependencies)
        + inspect.getsource(broker_runtime_topology)
        + inspect.getsource(runtime_session.RuntimeSession)
    )

    for required in (
        "MarketDataFlow",
        "StrategyExecutionPipeline",
        "TargetIntentProcessor",
        "OrderManagerActor",
        "ExecutionActor",
        "AccountActor",
    ):
        assert required in source
    assert "submit_order(" not in source


def test_backtest_order_path_routes_through_risk_engine_behaviorally(tmp_path: Path) -> None:
    # Behavioral parity guard (not source-substring): the backtest order path must
    # go THROUGH RiskEngine, not around it. A reject-all risk limit (notional far
    # below the order's ~1000 notional) must suppress every fill; a permissive
    # limit must let the *same* decision fill. A path that bypassed RiskEngine
    # would fill identically under both, so this difference proves risk is on the
    # shared chain.
    rejected = run_engine_streaming(
        BacktestEngine.from_config(
            _parity_config(max_notional="1"),
            bars=_flat_bars(),
            strategy=_BuyOnFirstBar(),
        ),
        tmp_path / "risk-reject-all",
    )
    assert rejected.fills == ()
    assert rejected.result.final_account.positions == {}

    permitted = run_engine_streaming(
        BacktestEngine.from_config(
            _parity_config(max_notional="1000000"),
            bars=_flat_bars(),
            strategy=_BuyOnFirstBar(),
        ),
        tmp_path / "risk-permit",
    )
    assert len(permitted.fills) == 1
    assert permitted.result.final_account.positions[_PARITY_INSTRUMENT].quantity == Decimal("10")


def test_backtest_public_runner_is_streaming_only() -> None:
    import qts.backtest.runner as runner

    cli_source = Path("scripts/run_backtest.py").read_text(encoding="utf-8")

    assert hasattr(runner, "run_backtest")
    assert not hasattr(runner, "run_streaming_backtest")
    assert not hasattr(runner, "StreamingBacktestRun")
    assert "--streaming" not in cli_source
