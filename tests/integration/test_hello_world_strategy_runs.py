"""Anchor: the GETTING_STARTED hello-world strategy actually runs through BacktestEngine.

Domain fact: OPT-66's onboarding promise is that a new user can copy
the strategy from the docs and drive it through the standard backtest
path — Strategy SDK → BacktestEngine → manifest with statistics. If
this anchor goes red the documented quickstart is misleading.

Owner: ``examples.strategies.hello_world.HelloWorldStrategy`` driven by
``qts.backtest.engine.BacktestEngine.run_streaming``.

Forbidden shortcut: bypassing BacktestEngine; testing the strategy
through a hand-rolled loop instead of the production backtest path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _uptrend_bars() -> list[Bar]:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return [
        Bar(
            instrument_id=_INSTRUMENT,
            start_time=start + timedelta(minutes=i),
            end_time=start + timedelta(minutes=i + 1),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal(100 + i),
            high=Decimal(100 + i),
            low=Decimal(100 + i),
            close=Decimal(100 + i),
            volume=Decimal("100"),
            is_complete=True,
        )
        for i in range(6)
    ]


def test_hello_world_strategy_produces_backtest_manifest(tmp_path: Path) -> None:
    from examples.strategies.hello_world import HelloWorldStrategy

    engine = BacktestEngine(
        strategy=HelloWorldStrategy(),
        bars=_uptrend_bars(),
        initial_cash=Decimal("100000"),
    )
    result = engine.run_streaming(tmp_path / "hello-world-run")

    manifest_path = Path(result.manifest_path)
    assert manifest_path.exists(), f"backtest manifest missing at {manifest_path}"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    # The strategy is documented as "buy first bar, hold to end". Under
    # the synthetic uptrend it must be profitable.
    statistics = payload.get("statistics") or payload.get("metrics") or {}
    assert "total_return" in statistics, f"manifest missing total_return: {statistics}"
    assert Decimal(str(statistics["total_return"])) > Decimal("0"), (
        f"hello-world should be profitable on uptrend, got {statistics['total_return']!r}"
    )
