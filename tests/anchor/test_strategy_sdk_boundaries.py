from __future__ import annotations

import ast
from pathlib import Path


def test_strategy_sdk_target_api_does_not_expose_risk_order_or_broker_internals() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef, StrategyContext

    ctx = StrategyContext()
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    intent = ctx.close(asset)

    assert not hasattr(ctx, "broker")
    assert not hasattr(ctx, "order_manager")
    assert not hasattr(ctx, "risk_engine")
    assert not hasattr(intent, "broker_symbol")
    assert not hasattr(intent, "contract_spec")


def test_gc_si_example_strategy_imports_only_strategy_sdk_and_standard_library() -> None:
    tree = ast.parse(Path("examples/strategies/gc_si_momentum.py").read_text(encoding="utf-8"))
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            module = node.module
            if module.startswith("qts.") and module != "qts.strategy_sdk":
                forbidden.append(module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("qts.") and alias.name != "qts.strategy_sdk":
                    forbidden.append(alias.name)

    assert forbidden == []
