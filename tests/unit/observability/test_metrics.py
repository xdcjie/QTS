from __future__ import annotations

from qts.observability.metrics import MetricsRegistry
from qts.runtime.mailbox import Mailbox


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
