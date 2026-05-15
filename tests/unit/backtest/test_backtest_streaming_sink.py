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


def test_backtest_runtime_event_sink_writes_events_and_manifest_contract(
    tmp_path: Path,
) -> None:
    import json

    from qts.core.ids import CorrelationId, RuntimeRunId
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext

    context = RuntimeEventContext(
        run_id=RuntimeRunId("bt-run-1"),
        mode="backtest",
        execution_environment="simulated",
    )
    writer = BacktestArtifactWriter(tmp_path, run_id=context.run_id)
    sink = BacktestRuntimeEventSink(writer, context=context)

    sink.write(
        RuntimeEvent(
            kind="runtime.market_data",
            payload={"instrument_id": "EQUITY.US.NASDAQ.AAPL"},
            correlation_id=CorrelationId("corr-bt-1"),
        )
    )
    sink.write_equity_point(
        EquityCurvePoint(
            time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            equity=Decimal("10000"),
        )
    )
    _, _, manifest, _ = writer.finalize(
        config_hash="cfg",
        dataset_metadata=(),
        cost_model={},
        processed_bars=1,
        warmup_bars=0,
        trading_bars=1,
        final_cash=Decimal("10000"),
        strategy_version="test",
    )

    events_path = next(tmp_path.glob("*.events.ndjson"))
    event_row = json.loads(events_path.read_text(encoding="utf-8").strip())
    assert event_row["run_id"] == "bt-run-1"
    assert event_row["mode"] == "backtest"
    assert event_row["sequence_no"] == 1
    assert event_row["execution_environment"] == "simulated"
    assert manifest["run_id"] == "bt-run-1"
    assert manifest["runtime_mode"] == "backtest"
    assert manifest["event_schema_version"] == RuntimeEvent.SCHEMA_VERSION
    assert manifest["artifacts"]["events"]["rows"] == 1


def test_backtest_runtime_event_sink_uses_deterministic_event_timestamps(
    tmp_path: Path,
) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext

    def write_once(output_dir: Path) -> dict[str, Any]:
        context = RuntimeEventContext(
            run_id=RuntimeRunId("bt-deterministic-events"),
            mode="backtest",
            execution_environment="simulated",
        )
        writer = BacktestArtifactWriter(output_dir, run_id=context.run_id)
        sink = BacktestRuntimeEventSink(writer, context=context)
        sink.write(
            RuntimeEvent(
                kind="runtime.market_data",
                payload={
                    "instrument_id": "EQUITY.US.NASDAQ.AAPL",
                    "timeframe": "1m",
                    "end_time": "2026-01-02T14:31:00+00:00",
                },
            )
        )
        sink.write_equity_point(
            EquityCurvePoint(
                time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
                equity=Decimal("10000"),
            )
        )
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
        return _read_ndjson_lines(next(output_dir.glob("*.events.ndjson")))[0]

    left = write_once(tmp_path / "left")
    right = write_once(tmp_path / "right")

    assert left["ts_event"] == right["ts_event"] == "1970-01-01T00:00:00.000001+00:00"
    assert left["event_hash"] == right["event_hash"]


def test_backtest_runtime_event_sink_requires_run_context(tmp_path: Path) -> None:
    import pytest
    from qts.reporting.backtest import BacktestArtifactWriter
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEvent

    sink = BacktestRuntimeEventSink(BacktestArtifactWriter(tmp_path))

    with pytest.raises(ValueError, match="run_id is required"):
        sink.write(RuntimeEvent(kind="runtime.state", payload={"state": "running"}))


def test_replay_anomalies_write_canonical_backtest_runtime_events(tmp_path: Path) -> None:
    from qts.core.ids import InstrumentId, RuntimeRunId
    from qts.data.provenance import ReplayDataAnomalyEvent, ReplayDataAnomalyType
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint
    from qts.runtime.market_data_flow import MarketDataFlow
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEventContext

    context = RuntimeEventContext(
        run_id=RuntimeRunId("bt-replay-anomalies"),
        mode="backtest",
        execution_environment="simulated",
    )
    writer = BacktestArtifactWriter(tmp_path, run_id=context.run_id)
    sink = BacktestRuntimeEventSink(writer, context=context)
    flow = MarketDataFlow(target_timeframe=None, exchange_timezone_by_instrument={})
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    for anomaly_type in (
        ReplayDataAnomalyType.DUPLICATE_DROPPED,
        ReplayDataAnomalyType.OUT_OF_ORDER_REJECTED,
        ReplayDataAnomalyType.GAP_DETECTED,
    ):
        result = flow.publish_source_event(
            ReplayDataAnomalyEvent(
                anomaly_type=anomaly_type,
                source_id="replay-source",
                instrument_id=instrument_id,
                timeframe="1m",
                bar_start=start,
                bar_end=start + timedelta(minutes=1),
                observed_at=start + timedelta(minutes=1),
                previous_end=start,
            )
        )
        for event in result.runtime_events:
            sink.write(event)

    sink.write_equity_point(
        EquityCurvePoint(time=start + timedelta(minutes=1), equity=Decimal("10000"))
    )
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

    rows = _read_ndjson_lines(next(tmp_path.glob("*.events.ndjson")))

    assert [row["kind"] for row in rows] == [
        "replay_duplicate_dropped",
        "replay_out_of_order_rejected",
        "runtime.degraded",
        "replay_gap_detected",
        "runtime.degraded",
    ]
    assert all(row["run_id"] == "bt-replay-anomalies" for row in rows)
    assert all(row["runtime_mode"] == "backtest" for row in rows)
    assert [row["sequence_no"] for row in rows] == [1, 2, 3, 4, 5]


def test_backtest_finalize_includes_runtime_topology_payload(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint

    topology = {
        "run_id": "bt-run-1",
        "mode": "backtest",
        "accounts": [],
        "strategies": [
            {
                "strategy_id": "strategy-a",
                "strategy_class": "tests.StrategyA",
                "account_id": "acct-a",
            }
        ],
        "broker_routes": [],
        "market_data_routes": [],
        "topology_hash": "sha256:example",
    }
    writer = BacktestArtifactWriter(tmp_path, run_id=RuntimeRunId("bt-run-1"))
    writer.write_equity_point(
        EquityCurvePoint(
            time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            equity=Decimal("10000"),
        )
    )

    _, _, manifest, _ = writer.finalize(
        config_hash="cfg",
        dataset_metadata=(),
        cost_model={},
        processed_bars=1,
        warmup_bars=0,
        trading_bars=1,
        final_cash=Decimal("10000"),
        strategy_version="test",
        runtime_topology_payload=topology,
    )

    assert manifest["runtime_topology"]["run_id"] == "bt-run-1"
    assert manifest["runtime_topology"]["topology_hash"] == "sha256:example"


def _read_ndjson_lines(path: Path) -> list[dict[str, Any]]:
    import json

    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
