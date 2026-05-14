from __future__ import annotations

import json
from pathlib import Path

from qts.runtime.sinks.base import RuntimeEvent


def test_live_runtime_event_sink_writes_stable_append_only_ndjson(tmp_path: Path) -> None:
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    first = sink.write(
        RuntimeEvent(
            kind="runtime.order_submitted",
            payload={
                "trace_id": "trace-1",
                "intent_id": "intent-1",
                "risk_decision_id": "risk-1",
                "order_id": "ord-1",
                "broker_order_id": "broker-1",
            },
        )
    )
    second = sink.write(
        RuntimeEvent(
            kind="runtime.order_submitted",
            payload={
                "broker_order_id": "broker-1",
                "order_id": "ord-1",
                "risk_decision_id": "risk-1",
                "intent_id": "intent-1",
                "trace_id": "trace-1",
            },
        )
    )
    sink.close()

    rows = [json.loads(line) for line in sink.path.read_text(encoding="utf-8").splitlines()]
    assert [row["sequence"] for row in rows] == [1, 2]
    assert rows[0]["event_hash"] == rows[1]["event_hash"]
    assert first.event_hash == second.event_hash
    assert sink.rows == 2
    assert sink.content_hash.startswith("sha256:")


def test_runtime_event_sink_writes_mode_and_execution_environment(tmp_path: Path) -> None:
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.write(
        RuntimeEvent(
            kind="runtime.order_submitted",
            payload={"order_id": "order-1"},
            mode="live",
            execution_environment="broker",
        )
    )
    sink.close()

    row = json.loads(sink.path.read_text(encoding="utf-8").strip())
    assert row["mode"] == "live"
    assert row["execution_environment"] == "broker"


def test_runtime_event_sink_writes_unified_runtime_envelope(tmp_path: Path) -> None:
    from qts.core.ids import (
        AccountId,
        CausationId,
        CorrelationId,
        EventId,
        InstrumentId,
        RuntimeRunId,
        StrategyId,
    )
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.write(
        RuntimeEvent(
            kind="runtime.fill_applied",
            payload={"fill_id": "fill-1"},
            event_id=EventId("evt-1"),
            run_id=RuntimeRunId("run-1"),
            mode="paper_broker",
            sequence_no=7,
            account_id=AccountId("DU1234567"),
            strategy_id=StrategyId("strategy-a"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            correlation_id=CorrelationId("corr-1"),
            causation_id=CausationId("evt-risk-1"),
            execution_environment="broker",
        )
    )
    sink.close()

    row = json.loads(sink.path.read_text(encoding="utf-8").strip())
    assert row["event_id"] == "evt-1"
    assert row["run_id"] == "run-1"
    assert row["sequence_no"] == 7
    assert row["account_id"] == "DU1234567"
    assert row["strategy_id"] == "strategy-a"
    assert row["instrument_id"] == "EQUITY.US.NASDAQ.AAPL"
    assert row["correlation_id"] == "corr-1"
    assert row["causation_id"] == "evt-risk-1"
    assert row["payload_schema_version"] == RuntimeEvent.SCHEMA_VERSION


def test_live_runtime_event_sink_rejects_secret_payload_values(tmp_path: Path) -> None:
    import pytest
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)

    with pytest.raises(ValueError, match="secret"):
        sink.write(RuntimeEvent(kind="runtime.error", payload={"password": "not-allowed"}))
