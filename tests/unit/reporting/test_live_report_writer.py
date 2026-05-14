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


def test_live_report_writer_includes_runtime_topology_payload(tmp_path: Path) -> None:
    from qts.core.ids import InstrumentId, RuntimeRunId
    from qts.reporting.live import LiveReportWriter
    from qts.runtime.config import LiveRuntimeConfig
    from qts.runtime.sinks.live import LiveRuntimeEventSink
    from qts.runtime.topology import RuntimeTopologyBuilder

    config = LiveRuntimeConfig(
        mode="paper_simulated",
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        allow_live_orders=False,
    )
    runtime_topology = RuntimeTopologyBuilder.from_live_config(
        config,
        RuntimeRunId("live-topology-test"),
        account_id="acct-paper",
        strategy_id="paper-strategy",
        strategy_class="examples.strategies.paper:PaperStrategy",
        subscriptions=(InstrumentId("F.US.CME.GC"),),
        base_currency="USD",
    )

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    manifest = LiveReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_simulated"},
        runtime_mode="paper_simulated",
        account_id="acct-paper",
        connection_metadata={"host": "127.0.0.1", "port": 4002},
        event_sink=sink,
        runtime_topology_payload=runtime_topology.to_manifest_payload(),
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))

    assert payload["runtime_topology"]["mode"] == "paper_simulated"
    assert payload["runtime_topology"]["account_count"] == 1
    assert payload["runtime_topology"]["strategy_count"] == 1
    assert payload["runtime_topology"]["topology_hash"].startswith("sha256:")


def test_live_report_writer_rejects_permission_mode_label(tmp_path: Path) -> None:
    import pytest
    from qts.reporting.live import LiveReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    with pytest.raises(ValueError, match="paper"):
        LiveReportWriter(tmp_path).write_manifest(
            config_payload={"mode": "paper"},
            runtime_mode="paper",
            account_id="DU1234567",
            connection_metadata={"host": "127.0.0.1", "port": 4002},
            event_sink=sink,
        )
