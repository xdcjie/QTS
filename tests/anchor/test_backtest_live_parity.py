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
    run_source = inspect.getsource(engine.BacktestEngine.run)

    for required in (
        "StrategyContext",
        "AccountActor",
        "OrderManagerActor",
        "ExecutionActor",
        "_BacktestExecutionAdapter",
    ):
        assert required in run_source
    assert "OrderRiskRequest" in engine_source
    assert ".check(" in engine_source
    assert "SubmitOrder" in engine_source
    assert "resolve_contract" in engine_source
    assert "ApplyFill" not in engine_source
