from __future__ import annotations

import json
from pathlib import Path

from qts.runtime.sinks.base import RuntimeEvent


def test_live_report_writer_manifest_names_artifacts_counts_and_redacted_connection(
    tmp_path: Path,
) -> None:
    from qts.reporting.live import LiveReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.write(RuntimeEvent(kind="runtime.state_transition", payload={"state": "running"}))
    sink.close()

    writer = LiveReportWriter(tmp_path)
    manifest = writer.write_manifest(
        config_payload={"mode": "paper_broker", "account_id": "DU1234567"},
        runtime_mode="paper_broker",
        account_id="DU1234567",
        market_data_environment="realtime",
        execution_environment="broker",
        account_environment="paper",
        broker_account_kind="paper",
        allow_live_orders=False,
        operator_signoff_id=None,
        connection_metadata={
            "host": "127.0.0.1",
            "port": 4002,
            "password": "should-not-render",
            "secret_ref": "ibkr/paper/password",
        },
        event_sink=sink,
        extra_artifacts={"reconciliation": tmp_path / "reconciliation.json"},
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))

    assert payload["runtime_mode"] == "paper_broker"
    assert payload["run_id"].startswith("live-")
    assert payload["event_schema_version"] == RuntimeEvent.SCHEMA_VERSION
    assert payload["account_id"] == "DU1234567"
    assert payload["market_data_environment"] == "realtime"
    assert payload["execution_environment"] == "broker"
    assert payload["account_environment"] == "paper"
    assert payload["broker_account_kind"] == "paper"
    assert payload["allow_live_orders"] is False
    assert payload["operator_signoff_id"] is None
    assert payload["config_hash"].startswith("sha256:")
    assert payload["artifacts"]["events"]["rows"] == 1
    assert payload["artifacts"]["events"]["sha256"] == sink.content_hash
    assert payload["artifacts"]["reconciliation"]["rows"] == 0
    assert payload["connection_metadata"] == {
        "host": "127.0.0.1",
        "port": 4002,
        "password": "<redacted>",
        "secret_ref": "<configured>",
    }
    assert "should-not-render" not in manifest.manifest_path.read_text(encoding="utf-8")
