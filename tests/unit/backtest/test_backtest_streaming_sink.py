from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar


def _bar(start: datetime, close: str = "100") -> Bar:
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


def test_backtest_streaming_sink_writes_orders_fills_ledger_and_points(tmp_path: Path) -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.execution.order_manager import (
        Order,
        OrderFill,
        OrderIntent,
        OrderSide,
    )
    from qts.execution.order_state_machine import OrderState
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink

    writer = BacktestArtifactWriter(tmp_path)
    sink = BacktestRuntimeEventSink(writer)
    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))

    order = Order(
        order_id=OrderId("bt-000001"),
        intent=OrderIntent(
            order_id=OrderId("bt-000001"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        ),
        state=OrderState.FILLED,
        broker_order_id="sim-000001",
    )
    fill = OrderFill(
        fill_id="sim-000001-fill-1",
        order_id=OrderId("bt-000001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("101"),
        commission=Decimal("0"),
        slippage=Decimal("0"),
    )

    sink.write_processed(orders=(order,), fills=(fill,), bar=bar)
    sink.write_equity_point(EquityCurvePoint(time=bar.end_time, equity=Decimal("10000")))

    writer.finalize(
        config_hash="cfg",
        dataset_metadata=(),
        cost_model={},
        processed_bars=1,
        warmup_bars=0,
        trading_bars=1,
        final_cash=Decimal("10000"),
        strategy_version="test",
    )

    orders_path = next(tmp_path.glob("*.orders.ndjson"))
    fills_path = next(tmp_path.glob("*.fills.ndjson"))
    ledger_path = next(tmp_path.glob("*.trade_ledger.ndjson"))
    equity_path = next(tmp_path.glob("*.equity_curve.ndjson"))

    assert orders_path.name.startswith("bt-")
    assert fills_path.name.startswith("bt-")
    assert ledger_path.name.startswith("bt-")
    assert equity_path.name.startswith("bt-")

    orders = _read_ndjson_lines(orders_path)
    fills = _read_ndjson_lines(fills_path)
    ledger = _read_ndjson_lines(ledger_path)
    equity = _read_ndjson_lines(equity_path)

    assert orders[0]["order_id"] == "bt-000001"
    assert orders[0]["state"] == "filled"
    assert fills[0]["fill_id"] == "sim-000001-fill-1"
    assert ledger[0]["order_id"] == "bt-000001"
    assert Decimal(ledger[0]["fill_price"]) == Decimal("101")
    assert equity[0]["equity"] == "10000"
    assert sink.order_count == 1


def _read_ndjson_lines(path: Path) -> list[dict[str, Any]]:
    import json

    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
