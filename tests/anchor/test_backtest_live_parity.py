from __future__ import annotations

import inspect
from pathlib import Path


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

    engine_source = inspect.getsource(engine.BacktestEngine)
    run_source = inspect.getsource(engine.BacktestEngine.run_streaming)
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.runtime.actors.order_manager_actor import OrderManagerActor
    from qts.runtime.execution_report_handler import ExecutionReportHandler
    from qts.runtime.intent_processing import OrderPlanBuilder, TargetIntentProcessor
    from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline

    actor_loop_source = inspect.getsource(BacktestActorLoop.run)
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
        assert required in actor_loop_source or required in engine_source
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
    assert "ApplyFill" in report_handler_source
    assert "ApplyFill" not in engine_source


def test_live_runtime_session_uses_shared_actor_chain() -> None:
    import qts.runtime.live_runtime_dependencies as live_runtime_dependencies
    import qts.runtime.live_runtime_session as live_runtime_session
    import qts.runtime.live_runtime_topology as live_runtime_topology

    source = (
        inspect.getsource(live_runtime_dependencies)
        + inspect.getsource(live_runtime_topology)
        + inspect.getsource(live_runtime_session.LiveRuntimeSession)
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


def test_backtest_public_runner_is_streaming_only() -> None:
    import qts.backtest.runner as runner

    cli_source = Path("scripts/run_backtest.py").read_text(encoding="utf-8")

    assert hasattr(runner, "run_backtest")
    assert not hasattr(runner, "run_streaming_backtest")
    assert not hasattr(runner, "StreamingBacktestRun")
    assert "--streaming" not in cli_source
