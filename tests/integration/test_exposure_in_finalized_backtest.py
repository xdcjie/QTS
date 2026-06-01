"""Integration anchor: avg_gross_exposure is present and non-zero after a real backtest."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar

from tests.support.backtest_streaming import run_engine_streaming


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


def test_finalized_backtest_emits_avg_gross_exposure(tmp_path: Path) -> None:
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class HoldFiveBarsStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.opened = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            if not self.opened:
                ctx.target_quantity(self.asset, Decimal("10"))
                self.opened = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            strategy=HoldFiveBarsStrategy(),
            bars=[_bar(start + timedelta(minutes=i), "100") for i in range(5)],
            initial_cash=Decimal("100000"),
        ),
        tmp_path / "exposure-run",
    )

    statistics = captured.manifest["metrics"]
    # avg_gross_exposure must be present and non-zero after the position opens.
    assert "avg_gross_exposure" in statistics
    assert Decimal(str(statistics["avg_gross_exposure"])) > Decimal("0")
    # avg_net_exposure is positive since the position is long.
    assert Decimal(str(statistics["avg_net_exposure"])) > Decimal("0")
