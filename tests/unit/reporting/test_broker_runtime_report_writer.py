from __future__ import annotations

import importlib
import json
from pathlib import Path

from qts.runtime.sinks.base import RuntimeEvent


def test_old_live_report_module_path_is_removed() -> None:
    import pytest

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("qts.reporting.live")


def test_broker_runtime_report_writer_manifest_names_artifacts_counts_and_redacted_connection(
    tmp_path: Path,
) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.base import RuntimeEventContext
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("live-report-test"), mode="paper_broker"),
    )
    sink.write(RuntimeEvent(kind="runtime.state_transition", payload={"state": "running"}))
    sink.close()

    writer = BrokerRuntimeReportWriter(tmp_path)
    manifest = writer.write_manifest(
        config_payload={"mode": "paper_broker", "account_id": "DU1234567"},
        runtime_mode="paper_broker",
        account_id="DU1234567",
        runtime_instance_id="paper-instance",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-paper",
        market_data_environment="realtime",
        execution_environment="broker",
        account_environment="paper",
        broker_account_kind="paper",
        live_order_permission=False,
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
    assert payload["run_id"].startswith("broker-runtime-")
    assert payload["event_schema_version"] == RuntimeEvent.SCHEMA_VERSION
    assert payload["account_id"] == "DU1234567"
    assert payload["market_data_environment"] == "realtime"
    assert payload["execution_environment"] == "broker"
    assert payload["account_environment"] == "paper"
    assert payload["broker_account_kind"] == "paper"
    assert payload["runtime_instance_id"] == "paper-instance"
    assert payload["live_order_permission"] is False
    assert payload["source_commit"] == "abcdef123456"
    assert payload["operator_identity_hash"] == "sha256:operator-paper"
    assert payload["startup_checklist_hash"].startswith("sha256:")
    assert payload["manifest_hash"].startswith("sha256:")
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


def test_broker_runtime_report_writer_includes_runtime_topology_payload(tmp_path: Path) -> None:
    from qts.core.ids import InstrumentId, RuntimeRunId
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
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

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_simulated"},
        runtime_mode="paper_simulated",
        account_id="acct-paper",
        runtime_instance_id="paper-sim-instance",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-paper",
        connection_metadata={"host": "127.0.0.1", "port": 4002},
        event_sink=sink,
        runtime_topology_payload=runtime_topology.to_manifest_payload(),
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))

    assert payload["runtime_topology"]["mode"] == "paper_simulated"
    assert payload["runtime_topology"]["account_count"] == 1
    assert payload["runtime_topology"]["strategy_count"] == 1
    assert payload["runtime_topology"]["topology_hash"].startswith("sha256:")


def test_broker_runtime_report_writer_manifest_includes_account_partition_topology(
    tmp_path: Path,
) -> None:
    from decimal import Decimal

    from qts.core.ids import AccountId, InstrumentId, RuntimeRunId, StrategyId
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.mode import RuntimeMode
    from qts.runtime.sinks.live import LiveRuntimeEventSink
    from qts.runtime.topology import (
        AccountRuntimeSpec,
        MarketDataRouteSpec,
        RuntimeTopology,
        StrategyRuntimeSpec,
    )

    account_a = AccountId("acct-report-a")
    account_b = AccountId("acct-report-b")
    runtime_topology = RuntimeTopology(
        run_id=RuntimeRunId("live-report-partition-topology"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("20000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-report-a"),
                strategy_class="tests.StrategyA",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-report-b"),
                strategy_class="tests.StrategyB",
                account_id=account_b,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.MSFT"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(
                    InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                    InstrumentId("EQUITY.US.NASDAQ.MSFT"),
                ),
            ),
        ),
    )

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_simulated"},
        runtime_mode="paper_simulated",
        account_id="multi-account",
        runtime_instance_id="paper-partition-instance",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-paper",
        connection_metadata={"host": "127.0.0.1", "port": 4002},
        event_sink=sink,
        runtime_topology_payload=runtime_topology.to_manifest_payload(),
    )

    payload = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
    partitions = payload["runtime_topology"]["account_partition_topology"]

    assert partitions == [
        {
            "account_id": "acct-report-a",
            "broker_route_count": 0,
            "strategy_ids": ["strat-report-a"],
        },
        {
            "account_id": "acct-report-b",
            "broker_route_count": 0,
            "strategy_ids": ["strat-report-b"],
        },
    ]


def test_paper_simulated_broker_runtime_manifest_includes_execution_assumptions(
    tmp_path: Path,
) -> None:
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_simulated"},
        runtime_mode="paper_simulated",
        account_id="acct-paper",
        runtime_instance_id="paper-assumptions-instance",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-paper",
        connection_metadata={"host": "127.0.0.1", "port": 4002},
        event_sink=sink,
    )

    assumptions = manifest.payload["execution_assumptions"]

    assert assumptions["fill_model_name"] == "immediate_market_fill"
    assert assumptions["slippage_model_name"] == "zero"
    assert assumptions["commission_model_name"] == "zero"
    assert assumptions["partial_fill_policy"] == "none"
    assert assumptions["broker_capability_model"]["broker_id"] == "simulated"
    assert assumptions["unsupported_order_rejection_policy"] == "reject_and_emit_runtime_event"


def test_broker_runtime_report_writer_rejects_permission_mode_label(tmp_path: Path) -> None:
    import pytest
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    with pytest.raises(ValueError, match="paper"):
        BrokerRuntimeReportWriter(tmp_path).write_manifest(
            config_payload={"mode": "paper"},
            runtime_mode="paper",
            account_id="DU1234567",
            runtime_instance_id="paper-label-instance",
            source_commit="abcdef123456",
            operator_identity_hash="sha256:operator-paper",
            connection_metadata={"host": "127.0.0.1", "port": 4002},
            event_sink=sink,
        )


def test_broker_runtime_report_writer_rejects_missing_operator_identity_hash(
    tmp_path: Path,
) -> None:
    import pytest
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    with pytest.raises(ValueError, match="operator_identity_hash"):
        BrokerRuntimeReportWriter(tmp_path).write_manifest(
            config_payload={"mode": "paper_broker"},
            runtime_mode="paper_broker",
            account_id="DU1234567",
            runtime_instance_id="paper-missing-operator",
            source_commit="abcdef123456",
            connection_metadata={"host": "127.0.0.1", "port": 4002},
            event_sink=sink,
        )
