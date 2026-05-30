"""``BacktestEngine`` orchestrates; it does not own collaborator construction.

QTS-FINAL-002 splits the engine so that runtime collaborators (execution
adapter, instrument context, portfolio projector, intent processor, dataset
manifest builder) are built by ``BacktestEngineAssembler``, and the engine only
holds and orchestrates them. These tests lock that delegation: construction
routes through the assembler, and the engine's collaborators are the identical
objects the assembler returned (not re-built inline).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from qts.backtest import engine_assembly
from qts.backtest.engine import BacktestEngine
from qts.backtest.engine_assembly import BacktestEngineAssembler, BacktestEngineCollaborators
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


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


class _NoopStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: object) -> None:
        return None


def _engine() -> BacktestEngine:
    return BacktestEngine(
        strategy=_NoopStrategy(),
        bars=[_bar()],
        initial_cash=Decimal("10000"),
    )


def test_engine_construction_delegates_to_assembler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[BacktestEngineCollaborators] = []
    original = BacktestEngineAssembler.collaborators

    def _spy(self: BacktestEngineAssembler, **kwargs: Any) -> BacktestEngineCollaborators:
        result = original(self, **kwargs)
        captured.append(result)
        return result

    monkeypatch.setattr(engine_assembly.BacktestEngineAssembler, "collaborators", _spy)

    engine = _engine()

    assert len(captured) == 1
    bundle = captured[0]
    # The engine holds the assembler's objects; it does not re-build them inline.
    assert engine._instrument_context is bundle.instrument_context
    assert engine._portfolio_projector is bundle.portfolio_projector
    assert engine._intent_processor is bundle.intent_processor
    assert engine._dataset_manifest_builder is bundle.dataset_manifest_builder
    assert engine._execution_adapter is bundle.execution_adapter
    assert engine._execution_timing is bundle.execution_timing


def test_engine_module_does_not_own_collaborator_imports() -> None:
    # The collaborator concrete types live with the assembler, not the engine
    # module: the engine should not import them to construct inline.
    import qts.backtest.engine as engine_mod

    for forbidden in (
        "BacktestInstrumentContext",
        "BacktestPortfolioProjector",
        "TargetIntentProcessor",
        "BacktestDatasetManifestBuilder",
        "SimulatedExecutionAdapter",
        "BacktestRiskPolicyFactory",
    ):
        assert not hasattr(engine_mod, forbidden), (
            f"{forbidden} should be owned by BacktestEngineAssembler, not imported into engine.py"
        )
