"""QTS-FINAL-004: the fill policy is part of a backtest run's report identity.

Two runs that differ only in fill-timing policy must produce different report
hashes, and the manifest must record the fill-timing honesty facts for every
run (including the default), so promotion gating cannot silently treat an
optimistic run as equivalent to a next-obtainable one.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy

from tests.support.backtest_engine import backtest_engine_from_inputs
from tests.support.backtest_streaming import run_engine_streaming

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _bar(minute: int, *, open_: str, close: str) -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=minute)
    low = min(Decimal(open_), Decimal(close))
    high = max(Decimal(open_), Decimal(close))
    return Bar(
        instrument_id=_INSTRUMENT,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(open_),
        high=high,
        low=low,
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def _bars() -> list[Bar]:
    return [
        _bar(0, open_="100", close="105"),
        _bar(1, open_="110", close="115"),
        _bar(2, open_="120", close="125"),
    ]


class _BuyOnce(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self._placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self._placed:
            ctx.target_quantity(self.asset, Decimal("10"))
            self._placed = True


def _run(timing: ExecutionTimingModel, output_dir: Path) -> Any:
    engine = backtest_engine_from_inputs(
        strategy=_BuyOnce(),
        bars=_bars(),
        initial_cash=Decimal("100000"),
        strategy_version="buy-once-v1",
        execution_timing=timing,
    )
    return run_engine_streaming(engine, output_dir)


def test_different_fill_policy_changes_report_hash(tmp_path: Path) -> None:
    next_bar = _run(ExecutionTimingModel.promotion_grade(), tmp_path / "next-bar-open")
    same_bar = _run(ExecutionTimingModel.research_only(), tmp_path / "same-bar-close")

    assert next_bar.result.report_hash != same_bar.result.report_hash


def test_manifest_records_fill_identity_for_default_run(tmp_path: Path) -> None:
    captured = _run(ExecutionTimingModel.promotion_grade(), tmp_path / "default")
    assumptions = captured.manifest["execution_assumptions"]

    assert assumptions["fill_policy"] == "next_bar_open"
    assert assumptions["promotion_grade"] is True
    assert assumptions["optimistic"] is False
