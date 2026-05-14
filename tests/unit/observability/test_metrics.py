from __future__ import annotations

import ast
from pathlib import Path

from qts.core.ids import CorrelationId
from qts.observability.metrics import MetricsRegistry, RuntimeCounterMetric, RuntimeLatencyMetric
from qts.runtime.mailbox import Mailbox
from qts.runtime.sinks.base import RuntimeEvent


def test_metrics_registry_records_counters_gauges_and_queue_health() -> None:
    metrics = MetricsRegistry()
    mailbox = Mailbox()
    mailbox.put("message")

    metrics.increment("risk.rejections", tags={"account_id": "acct-a"})
    metrics.observe_queue("orders", mailbox, oldest_message_lag_seconds=1.5)

    snapshot = metrics.snapshot()
    assert snapshot["risk.rejections{account_id=acct-a}"] == 1
    assert snapshot["queue.depth{name=orders}"] == 1
    assert snapshot["queue.oldest_lag_seconds{name=orders}"] == 1.5


def test_metrics_registry_keeps_private_key_formatting_inside_the_class() -> None:
    tree = ast.parse(Path("backend/src/qts/observability/metrics.py").read_text(encoding="utf-8"))
    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_metric_key" not in private_functions


def test_metrics_registry_defines_runtime_counter_and_latency_metrics() -> None:
    assert RuntimeCounterMetric.RISK_REJECTIONS_TOTAL.value == "risk_rejections_total"
    assert RuntimeCounterMetric.MARKET_DATA_STALE_TOTAL.value == "market_data_stale_total"
    assert RuntimeCounterMetric.MARKET_DATA_SUBSCRIPTION_FAILURES_TOTAL.value == (
        "market_data_subscription_failures_total"
    )
    assert RuntimeCounterMetric.RUNTIME_RECOVERY_BLOCKS_TOTAL.value == (
        "runtime_recovery_blocks_total"
    )
    assert RuntimeLatencyMetric.FILL_TO_ACCOUNT_APPLY_LATENCY.value == (
        "fill_to_account_apply_latency"
    )


def test_metrics_increment_on_risk_rejection() -> None:
    metrics = MetricsRegistry()
    metrics.record_runtime_event(
        RuntimeEvent(
            kind="risk.rejected",
            payload={"reason_code": "MAX_QTY_EXCEEDED"},
            correlation_id=CorrelationId("corr-1"),
        )
    )

    snapshot = metrics.snapshot()
    assert snapshot["risk_rejections_total{reason_code=MAX_QTY_EXCEEDED}"] == 1


def test_metrics_increment_on_market_data_events() -> None:
    metrics = MetricsRegistry()

    metrics.record_runtime_event(RuntimeEvent(kind="market_data.bar.closed", payload={}))
    metrics.record_runtime_event(RuntimeEvent(kind="runtime.market_data", payload={}))

    snapshot = metrics.snapshot()
    assert snapshot["market_data_events_total"] == 2


def test_metrics_increment_on_market_data_subscription_failure_and_recovery_block() -> None:
    metrics = MetricsRegistry()
    metrics.record_runtime_event(
        RuntimeEvent(
            kind="market_data_subscription_failed",
            payload={"reason_code": "MARKET_DATA_SUBSCRIPTION_FAILED"},
        )
    )
    metrics.record_runtime_event(
        RuntimeEvent(
            kind="runtime.recovery_blocked",
            payload={"reason_code": "EVENT_SEQUENCE_GAP"},
        )
    )

    snapshot = metrics.snapshot()
    assert (
        snapshot[
            "market_data_subscription_failures_total{reason_code=MARKET_DATA_SUBSCRIPTION_FAILED}"
        ]
        == 1
    )
    assert snapshot["runtime_recovery_blocks_total{reason_code=EVENT_SEQUENCE_GAP}"] == 1
