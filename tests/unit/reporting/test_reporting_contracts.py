from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.runtime.sinks.base import RuntimeEvent


def test_reporting_base_contracts_define_manifest_and_artifact_methods() -> None:
    from qts.reporting.base import ReportWriter, RuntimeArtifactWriter, RuntimeManifest

    assert hasattr(RuntimeManifest, "from_payload")
    for method_name in ("write_manifest", "finalize"):
        assert hasattr(ReportWriter, method_name)
    for method_name in ("write_event", "write_snapshot", "write_manifest", "finalize"):
        assert hasattr(RuntimeArtifactWriter, method_name)


def test_live_manifest_validates_against_shared_runtime_manifest(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.base import RuntimeManifest
    from qts.reporting.live import LiveReportWriter
    from qts.runtime.sinks.base import RuntimeEventContext
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("live-shared-manifest"), mode="live"),
    )
    sink.write(RuntimeEvent(kind="runtime.state_transition", payload={"state": "running"}))
    sink.close()

    manifest = LiveReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "live"},
        runtime_mode="live",
        account_id="acct-live",
        connection_metadata={"host": "127.0.0.1", "port": 4001},
        event_sink=sink,
        runtime_topology_payload={"topology_hash": "sha256:live-topology"},
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
    runtime_manifest = RuntimeManifest.from_payload(payload)

    assert runtime_manifest.run_id == payload["run_id"]
    assert runtime_manifest.runtime_mode == "live"
    assert runtime_manifest.event_schema_version == RuntimeEvent.SCHEMA_VERSION
    assert runtime_manifest.artifact_schema_version == "1"
    assert runtime_manifest.config_hash.startswith("sha256:")
    assert runtime_manifest.topology_hash == "sha256:live-topology"
    assert runtime_manifest.created_at.tzinfo is not None
    assert runtime_manifest.finalized_at.tzinfo is not None


def test_backtest_manifest_validates_against_shared_runtime_manifest(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint
    from qts.reporting.base import RuntimeManifest

    writer = BacktestArtifactWriter(tmp_path, run_id=RuntimeRunId("bt-shared-manifest"))
    writer.write_runtime_event(
        {
            "run_id": "bt-shared-manifest",
            "runtime_mode": "backtest",
            "sequence_no": 1,
            "event_id": "event-1",
            "payload_schema_version": RuntimeEvent.SCHEMA_VERSION,
        }
    )
    writer.write_equity_point(
        EquityCurvePoint(time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), equity=Decimal("10000"))
    )

    _run_id, _report_hash, payload, _artifacts = writer.finalize(
        config_hash="sha256:config",
        dataset_metadata=(),
        cost_model={},
        processed_bars=1,
        warmup_bars=0,
        trading_bars=1,
        final_cash=Decimal("10000"),
        strategy_version="test",
        runtime_topology_payload={"topology_hash": "sha256:backtest-topology"},
    )
    runtime_manifest = RuntimeManifest.from_payload(payload)

    assert runtime_manifest.run_id == "bt-shared-manifest"
    assert runtime_manifest.runtime_mode == "backtest"
    assert runtime_manifest.event_schema_version == RuntimeEvent.SCHEMA_VERSION
    assert runtime_manifest.artifact_schema_version == "1"
    assert runtime_manifest.config_hash == "sha256:config"
    assert runtime_manifest.topology_hash == "sha256:backtest-topology"
