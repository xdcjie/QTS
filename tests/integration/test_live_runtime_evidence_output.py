from __future__ import annotations

import json
from pathlib import Path

from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.topology import RuntimeTopologyBuilder


def test_live_runtime_evidence_output_links_event_stream_and_manifest(tmp_path: Path) -> None:
    from qts.core.ids import InstrumentId, RuntimeRunId
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.config import LiveRuntimeConfig
    from qts.runtime.sinks.base import RuntimeEventContext
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    topology = RuntimeTopologyBuilder.from_live_config(
        LiveRuntimeConfig(
            mode="paper_simulated",
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=False,
        ),
        RuntimeRunId("live-evidence-1"),
        account_id="DU1234567",
        strategy_id="paper-evidence-strategy",
        strategy_class="tests.integration.test_live_runtime_evidence_output:NoopPaperStrategy",
        subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
    )

    sink = LiveRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("live-evidence-1"), mode="paper_broker"),
    )
    sink.write(RuntimeEvent(kind="runtime.market_data", payload={"instrument_id": "AAPL"}))
    sink.write(RuntimeEvent(kind="runtime.account_snapshot", payload={"cash": {"USD": "1000"}}))
    sink.close()

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_broker"},
        runtime_mode="paper_broker",
        account_id="DU1234567",
        runtime_instance_id="live-evidence-runtime-instance",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-live-evidence",
        connection_metadata={"host": "127.0.0.1", "port": 4002},
        event_sink=sink,
        runtime_topology_payload=topology.to_manifest_payload(),
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))

    assert payload["artifacts"]["events"]["path"] == str(sink.path)
    assert payload["artifacts"]["events"]["rows"] == 2
    assert payload["report_hash"].startswith("sha256:")
    assert payload["runtime_topology"]["mode"] == "paper_simulated"
    assert payload["runtime_topology"]["strategy_count"] == 1
    assert payload["runtime_topology"]["topology_hash"].startswith("sha256:")


class NoopPaperStrategy:
    pass
