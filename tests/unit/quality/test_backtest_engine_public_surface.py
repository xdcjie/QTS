"""QTS-FINAL-002: backtest modules do not re-export runtime actor symbols.

``PublicSurfaceRule`` rejects runtime-actor symbols appearing in a backtest
module's ``__all__``; the production ``qts.backtest.engine`` surface is limited
to its own types.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules import PublicSurfaceRule


def _check(qts_relative: str, source: str) -> list[str]:
    tree = ast.parse(source)
    violations = PublicSurfaceRule().check(
        relative_path=Path("backend/src/qts") / qts_relative,
        qts_relative_path=Path(qts_relative),
        tree=tree,
    )
    return [v.message for v in violations]


def test_flags_runtime_actor_symbol_in_backtest_all() -> None:
    source = (
        "from qts.runtime.actors.strategy_actor import StrategyActor\n"
        '__all__ = ["BacktestEngine", "StrategyActor"]\n'
    )
    messages = _check("backtest/engine.py", source)
    assert any("StrategyActor" in m for m in messages)


def test_allows_own_symbols_in_backtest_all() -> None:
    source = (
        "from qts.runtime.actors.account_actor import AccountSnapshot\n"
        "class BacktestStreamResult:\n"
        "    pass\n"
        '__all__ = ["BacktestEngine", "BacktestStreamResult"]\n'
    )
    # AccountSnapshot is imported but not exported -> no violation.
    assert _check("backtest/engine.py", source) == []


def test_does_not_apply_outside_backtest() -> None:
    source = (
        'from qts.runtime.actors.strategy_actor import StrategyActor\n__all__ = ["StrategyActor"]\n'
    )
    assert _check("runtime/sample.py", source) == []


def test_production_backtest_engine_all_has_no_runtime_actors() -> None:
    from qts.backtest import engine as engine_module

    actor_names = {
        "StrategyActor",
        "SignalAggregatorActor",
        "StrategyBarEvent",
        "StrategyBarResult",
        "StrategyFinalize",
        "StrategyFinalized",
        "AggregatedSignalBatch",
        "StrategySignalEvent",
    }
    assert set(engine_module.__all__).isdisjoint(actor_names)
    assert set(engine_module.__all__) == {
        "BacktestCostModel",
        "BacktestEngine",
        "BacktestStreamResult",
    }


def test_public_surface_rule_passes_for_production_engine() -> None:
    path = Path("backend/src/qts/backtest/engine.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations = PublicSurfaceRule().check(
        relative_path=path,
        qts_relative_path=Path("backtest/engine.py"),
        tree=tree,
    )
    assert violations == []
