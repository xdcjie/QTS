from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy

from tests.support.backtest_streaming import run_engine_streaming


def _bar(start: datetime, close: Decimal) -> Bar:
    from qts.core.ids import InstrumentId

    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=close,
        high=close,
        low=close,
        close=close,
        volume=Decimal("100"),
        is_complete=True,
    )


class OneOrderStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.placed:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.placed = True


def test_backtest_streaming_emits_stable_artifacts(tmp_path: Path) -> None:
    from tests.support.backtest_engine import backtest_engine_from_inputs

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [
        _bar(start + timedelta(minutes=offset), Decimal("100") + Decimal(offset))
        for offset in range(2)
    ]

    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            strategy=OneOrderStrategy(),
            bars=bars,
            initial_cash=Decimal("10000"),
            # Characterizes artifact stability, not fill timing; pin same-bar.
            execution_timing=ExecutionTimingModel.research_only(),
        ),
        tmp_path / "streaming-characterization",
    )

    assert captured.result.processed_bars == 2
    assert captured.result.trading_bars == 2
    assert captured.result.warmup_bars == 0
    assert captured.result.report_hash == captured.manifest["report_hash"]

    assert captured.result.run_id.value == captured.manifest["run_id"]
    assert captured.manifest["artifacts"].keys() == {
        "events",
        "equity_curve",
        "fills",
        "orders",
        "statistics",
        "trade_ledger",
    }
    assert captured.result.artifact_rows == {
        "events": 11,
        "orders": 1,
        "fills": 1,
        "statistics": 1,
        "trade_ledger": 1,
        "equity_curve": 2,
    }
    for kind, artifact in captured.manifest["artifacts"].items():
        assert artifact["rows"] == captured.result.artifact_rows[kind]
        assert artifact["path"]
        assert artifact["sha256"].startswith("sha256:")

    assert len(captured.orders) == 1
    assert captured.orders[0]["state"] == "filled"
    fill_event = next(event for event in captured.events if event["kind"] == "runtime.fill_applied")
    assert fill_event["payload"]["client_order_id"] == "bt-client-000001"
    assert (
        fill_event["correlation_id"]
        == next(event for event in captured.events if event["kind"] == "runtime.order_submitted")[
            "correlation_id"
        ]
    )
    assert captured.fills
    assert captured.trade_ledger and len(captured.trade_ledger) == 1
    assert Decimal(captured.trade_ledger[0]["fill_price"]) == Decimal("100")
    assert Decimal(captured.equity_curve[0]["equity"]) == Decimal("10000")
