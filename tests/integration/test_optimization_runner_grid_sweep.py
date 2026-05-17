"""Integration anchor: OptimizationRunner runs a parameter grid sequentially.

Domain fact: the optimizer is a thin orchestrator over BacktestEngine.
Each parameter combination produces a distinct backtest manifest hash and
captures the configured objective metric from the resulting statistics
payload. Results are ranked by objective descending.

Owner: ``qts.research.optimizer.runner.OptimizationRunner``.

Forbidden shortcut: bypassing BacktestEngine; sharing strategy state across
runs; treating manifest_hash differences as test noise.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar
from qts.research.optimizer import (
    OptimizationJob,
    OptimizationRunner,
    ParameterGrid,
    ParameterSpace,
)


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


def _bars_factory() -> list[Bar]:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return [_bar(start + timedelta(minutes=i), str(100 + i)) for i in range(8)]


def _strategy_factory(params: dict[str, Any]):  # type: ignore[no-untyped-def]
    from qts.strategy_sdk import Strategy

    class _ParameterizedStrategy(Strategy):
        def __init__(self) -> None:
            self.target_quantity = Decimal(str(params["target_quantity"]))
            self.entry_bar = int(params["entry_bar"])
            self._bar_index = 0
            self._opened = False

        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            self._bar_index += 1
            if not self._opened and self._bar_index >= self.entry_bar:
                ctx.target_quantity(self.asset, self.target_quantity)
                self._opened = True

    return _ParameterizedStrategy()


def test_grid_sweep_produces_distinct_runs_ranked_by_objective(tmp_path: Path) -> None:
    job = OptimizationJob(
        strategy_factory=_strategy_factory,
        bars_factory=_bars_factory,
        initial_cash=Decimal("100000"),
        parameter_grid=ParameterGrid(
            ParameterSpace(name="target_quantity", values=(Decimal("1"), Decimal("2"))),
            ParameterSpace(name="entry_bar", values=(1, 2)),
        ),
        objective_metric="total_return",
        output_root=tmp_path / "optimizer-runs",
    )

    runner = OptimizationRunner()
    results = runner.run(job)

    assert len(results) == 4
    # Distinct manifests per run.
    manifest_hashes = {result.manifest_hash for result in results}
    assert len(manifest_hashes) == 4
    # Each result records the parameters.
    parameter_sets = [tuple(sorted(result.parameters.items())) for result in results]
    assert len(set(parameter_sets)) == 4
    # Results are ranked by objective descending.
    objectives = [result.objective_value for result in results]
    assert objectives == sorted(objectives, reverse=True)
    # The top result's objective is at least as large as the worst's.
    assert results[0].objective_value >= results[-1].objective_value
