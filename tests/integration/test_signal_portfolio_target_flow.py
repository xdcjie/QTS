from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import (
    EqualWeightSignalPortfolioConstruction,
    Signal,
    SignalDirection,
    Strategy,
)

from tests.support.backtest_engine import backtest_engine_from_inputs
from tests.support.backtest_streaming import run_engine_streaming

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


class SignalDrivenStrategy(Strategy):
    """Strategy that reaches order flow through Signal -> TargetIntent."""

    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.constructed = False

    def on_bar(self, ctx: Any, bar: Bar) -> None:
        if self.constructed:
            return
        ctx.emit_signal(
            Signal(
                asset=self.asset,
                direction=SignalDirection.UP,
                generated_at=bar.end_time,
                horizon=timedelta(days=1),
                source_model="integration-smoke",
            )
        )
        ctx.construct_targets(EqualWeightSignalPortfolioConstruction(gross_exposure=Decimal("0.5")))
        self.constructed = True


def _bar(start: datetime, close: str = "100") -> Bar:
    price = Decimal(close)
    return Bar(
        instrument_id=_INSTRUMENT,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal("100"),
        is_complete=True,
    )


def test_signal_portfolio_construction_targets_enter_existing_backtest_path(
    tmp_path: Path,
) -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            strategy=SignalDrivenStrategy(),
            bars=[_bar(start), _bar(start + timedelta(minutes=1))],
            initial_cash=Decimal("1000"),
        ),
        tmp_path / "signal-target-flow",
    )

    assert len(captured.orders) == 1
    assert len(captured.fills) == 1
    assert captured.result.final_account.positions[_INSTRUMENT].quantity == Decimal("5")
    assert captured.result.final_account.cash["USD"] == Decimal("500")
