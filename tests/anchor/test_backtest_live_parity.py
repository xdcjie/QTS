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
    from qts.backtest.intent_processor import BacktestIntentProcessor

    actor_loop_source = inspect.getsource(BacktestActorLoop.run)
    processor_source = inspect.getsource(BacktestIntentProcessor)

    assert "BacktestActorLoop" in run_source

    for required in (
        "StrategyContext",
        "AccountActor",
        "OrderManagerActor",
        "ExecutionActor",
        "_BacktestExecutionAdapter",
    ):
        assert required in actor_loop_source or required in engine_source
    assert "OrderRiskRequest" in processor_source
    assert ".check(" in processor_source or ".check" in processor_source
    assert "SubmitOrder" in processor_source
    assert "order_instrument_for_intent" in processor_source
    assert "market_price_for_intent" in processor_source
    assert "ApplyFill" not in engine_source


def test_backtest_public_runner_is_streaming_only() -> None:
    import qts.backtest.runner as runner

    cli_source = Path("scripts/run_backtest.py").read_text(encoding="utf-8")

    assert hasattr(runner, "run_backtest")
    assert not hasattr(runner, "run_streaming_backtest")
    assert not hasattr(runner, "StreamingBacktestRun")
    assert "--streaming" not in cli_source
