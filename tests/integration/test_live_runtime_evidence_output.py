from __future__ import annotations

import json
from pathlib import Path

from qts.runtime.sinks.base import RuntimeEvent


def test_live_runtime_evidence_output_links_event_stream_and_manifest(tmp_path: Path) -> None:
    from qts.reporting.live import LiveReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.write(RuntimeEvent(kind="runtime.market_data", payload={"instrument_id": "AAPL"}))
    sink.write(RuntimeEvent(kind="runtime.account_snapshot", payload={"cash": {"USD": "1000"}}))
    sink.close()

    manifest = LiveReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper"},
        runtime_mode="paper",
        account_id="DU1234567",
        connection_metadata={"host": "127.0.0.1", "port": 4002},
        event_sink=sink,
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))

    assert payload["artifacts"]["events"]["path"] == str(sink.path)
    assert payload["artifacts"]["events"]["rows"] == 2
    assert payload["report_hash"].startswith("sha256:")
