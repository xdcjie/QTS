from __future__ import annotations

import runpy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy

EXAMPLE_STRATEGY_PATH = Path("examples/strategies/moving_average_cross.py")


def _load_moving_average_cross() -> type[Strategy]:
    namespace = runpy.run_path(str(EXAMPLE_STRATEGY_PATH))
    return cast(type[Strategy], namespace["MovingAverageCross"])


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


def test_example_moving_average_strategy_runs_in_backtest_mode() -> None:
    from qts.backtest.engine import BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start + timedelta(minutes=i), Decimal("100") + Decimal(i)) for i in range(65)]

    result = BacktestEngine(
        strategy=_load_moving_average_cross()(),
        bars=bars,
        initial_cash=Decimal("100000"),
    ).run()

    assert result.processed_bars == 65
    assert result.orders


def test_example_strategy_imports_only_strategy_sdk() -> None:
    source = EXAMPLE_STRATEGY_PATH.read_text()

    assert "qts.runtime" not in source
    assert "qts.risk" not in source
    assert "qts.execution" not in source
    assert "qts.strategy_sdk" in source
