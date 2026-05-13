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


def test_live_runtime_event_sink_rejects_secret_payload_values(tmp_path: Path) -> None:
    import pytest
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)

    with pytest.raises(ValueError, match="secret"):
        sink.write(RuntimeEvent(kind="runtime.error", payload={"password": "not-allowed"}))
