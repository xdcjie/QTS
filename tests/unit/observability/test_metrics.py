from __future__ import annotations

import ast
from pathlib import Path

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


def test_metrics_registry_keeps_private_key_formatting_inside_the_class() -> None:
    tree = ast.parse(Path("backend/src/qts/observability/metrics.py").read_text(encoding="utf-8"))
    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_metric_key" not in private_functions
