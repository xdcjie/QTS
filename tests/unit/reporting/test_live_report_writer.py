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
        config_payload={"mode": "paper", "account_id": "DU1234567"},
        runtime_mode="paper",
        account_id="DU1234567",
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

    assert payload["runtime_mode"] == "paper"
    assert payload["account_id"] == "DU1234567"
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
