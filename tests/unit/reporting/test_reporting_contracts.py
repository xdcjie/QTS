from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.runtime.sinks.base import RuntimeEvent

from tests.support.backtest_manifest import m1_manifest_kwargs


def _canonical_manifest_payload() -> dict[str, object]:
    return {
        "run_id": "run-canonical",
        "runtime_instance_id": "instance-canonical",
        "runtime_mode": "paper_broker",
        "market_data_environment": "realtime",
        "execution_environment": "broker",
        "account_environment": "paper",
        "order_submission_permission": False,
        "config_hash": "sha256:config",
        "topology_hash": "sha256:topology",
        "startup_checklist_hash": "sha256:startup",
        "event_schema_version": RuntimeEvent.SCHEMA_VERSION,
        "artifact_schema_version": "1",
        "platform_baseline_version": "qts-platform-v1",
        "created_at": "2026-01-02T14:30:00+00:00",
        "source_commit": "abcdef123456",
        "operator_identity_hash": "sha256:operator",
    }


def test_reporting_base_contracts_define_manifest_and_artifact_methods() -> None:
    from qts.reporting.base import (
        ReportWriter,
        RuntimeArtifactWriter,
        RuntimeManifest,
        RuntimeManifestRecord,
    )

    assert hasattr(RuntimeManifest, "from_payload")
    assert hasattr(RuntimeManifest, "manifest_hash")
    assert hasattr(RuntimeManifestRecord, "load")
    assert hasattr(RuntimeManifestRecord, "query")
    for method_name in ("write_manifest", "finalize"):
        assert hasattr(ReportWriter, method_name)
    for method_name in ("write_event", "write_snapshot", "write_manifest", "finalize"):
        assert hasattr(RuntimeArtifactWriter, method_name)


def test_runtime_manifest_rejects_missing_canonical_required_field() -> None:
    import pytest
    from qts.reporting.base import RuntimeManifest

    payload = _canonical_manifest_payload()
    del payload["startup_checklist_hash"]

    with pytest.raises(ValueError, match="startup_checklist_hash"):
        RuntimeManifest.from_payload(payload)


def test_runtime_manifest_record_loads_queryable_deterministic_hash(tmp_path: Path) -> None:
    from qts.reporting.base import RuntimeManifestRecord

    payload = _canonical_manifest_payload()
    first_path = tmp_path / "first.manifest.json"
    second_path = tmp_path / "second.manifest.json"
    first_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    second_path.write_text(json.dumps(dict(reversed(tuple(payload.items())))), encoding="utf-8")

    first = RuntimeManifestRecord.load(first_path)
    second = RuntimeManifestRecord.load(second_path)

    assert first.manifest_hash == second.manifest_hash
    assert first.query("run_id") == "run-canonical"
    assert first.query("runtime_mode") == "paper_broker"
    assert first.query("manifest_hash") == first.manifest_hash


def test_backtest_manifest_contains_platform_baseline_version(tmp_path: Path) -> None:
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint
    from qts.reporting.base import PLATFORM_BASELINE_VERSION, RuntimeManifest

    writer = BacktestArtifactWriter(tmp_path)
    writer.write_equity_point(
        EquityCurvePoint(time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC), equity=Decimal("10000"))
    )
    _, _, payload, _ = writer.finalize(
        config_hash="sha256:config",
        **m1_manifest_kwargs(),
        cost_model={},
        processed_bars=1,
        warmup_bars=0,
        trading_bars=1,
        final_cash=Decimal("10000"),
        strategy_version="test",
    )

    runtime_manifest = RuntimeManifest.from_payload(payload)

    assert runtime_manifest.platform_baseline_version == PLATFORM_BASELINE_VERSION
    assert runtime_manifest.platform_baseline_version == payload["platform_baseline_version"]


def test_broker_runtime_manifest_contains_platform_baseline_version(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.base import PLATFORM_BASELINE_VERSION, RuntimeManifest
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.base import RuntimeEventContext
    from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink

    sink = BrokerRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("broker-baseline"), mode="paper_broker"),
    )
    sink.close()
    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_broker"},
        runtime_mode="paper_broker",
        account_id="acct-baseline",
        runtime_instance_id="broker-baseline-instance",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-baseline",
        connection_metadata={},
        event_sink=sink,
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
    runtime_manifest = RuntimeManifest.from_payload(payload)

    assert runtime_manifest.platform_baseline_version == PLATFORM_BASELINE_VERSION
    assert payload["platform_baseline_version"] == PLATFORM_BASELINE_VERSION


def test_broker_runtime_manifest_validates_against_shared_runtime_manifest(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.base import RuntimeManifest
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.base import RuntimeEventContext
    from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink

    sink = BrokerRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("live-shared-manifest"), mode="live"),
    )
    sink.write(RuntimeEvent(kind="runtime.state_transition", payload={"state": "running"}))
    sink.close()

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "live"},
        runtime_mode="live",
        account_id="acct-live",
        runtime_instance_id="live-instance",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-live",
        connection_metadata={"host": "127.0.0.1", "port": 4001},
        event_sink=sink,
        runtime_topology_payload={"topology_hash": "sha256:live-topology"},
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
    runtime_manifest = RuntimeManifest.from_payload(payload)

    assert runtime_manifest.run_id == payload["run_id"]
    assert runtime_manifest.runtime_instance_id == "live-instance"
    assert runtime_manifest.runtime_mode == "live"
    assert runtime_manifest.market_data_environment == "unknown"
    assert runtime_manifest.execution_environment == "unknown"
    assert runtime_manifest.account_environment == "unknown"
    assert runtime_manifest.order_submission_permission is False
    assert runtime_manifest.event_schema_version == RuntimeEvent.SCHEMA_VERSION
    assert runtime_manifest.artifact_schema_version == "1"
    assert runtime_manifest.config_hash.startswith("sha256:")
    assert runtime_manifest.topology_hash == "sha256:live-topology"
    assert runtime_manifest.startup_checklist_hash.startswith("sha256:")
    assert runtime_manifest.source_commit == "abcdef123456"
    assert runtime_manifest.operator_identity_hash == "sha256:operator-live"
    assert runtime_manifest.manifest_hash.startswith("sha256:")
    assert runtime_manifest.created_at.tzinfo is not None


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
    manifest_kwargs = m1_manifest_kwargs()
    manifest_kwargs["runtime_topology_payload"] = {"topology_hash": "sha256:backtest-topology"}

    _run_id, _report_hash, payload, _artifacts = writer.finalize(
        config_hash="sha256:config",
        **manifest_kwargs,
        cost_model={},
        processed_bars=1,
        warmup_bars=0,
        trading_bars=1,
        final_cash=Decimal("10000"),
        strategy_version="test",
    )
    runtime_manifest = RuntimeManifest.from_payload(payload)

    assert runtime_manifest.run_id == "bt-shared-manifest"
    assert runtime_manifest.runtime_instance_id == "bt-shared-manifest"
    assert runtime_manifest.runtime_mode == "backtest"
    assert runtime_manifest.market_data_environment == "historical_replay"
    assert runtime_manifest.execution_environment == "simulated"
    assert runtime_manifest.account_environment == "simulated"
    assert runtime_manifest.order_submission_permission is False
    assert runtime_manifest.event_schema_version == RuntimeEvent.SCHEMA_VERSION
    assert runtime_manifest.artifact_schema_version == "1"
    assert runtime_manifest.config_hash == "sha256:config"
    assert runtime_manifest.topology_hash == "sha256:backtest-topology"
    assert runtime_manifest.startup_checklist_hash == "sha256:not-applicable-backtest"
    assert runtime_manifest.source_commit == "not-applicable-backtest"
    assert runtime_manifest.operator_identity_hash == "sha256:not-applicable-backtest"
    assert runtime_manifest.manifest_hash == payload["manifest_hash"]
