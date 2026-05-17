"""Anchor: docs/operations/observability_setup.md references every shipped alert.

Domain fact: the doc is the operator-facing index of alerts + metrics +
runbook links. A new alert without a doc reference becomes invisible to
the on-call rotation; a doc that lists a non-existent alert becomes
stale.

Owner: ``docs/operations/observability_setup.md``.

Forbidden shortcut: documenting metrics that the runtime doesn't
actually emit; alerts in YAML without a matching doc entry.
"""

from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]

_ALERTS_PATH = Path("configs/alerts/qts_alerts.yaml")
_DOC_PATH = Path("docs/operations/observability_setup.md")


def test_observability_doc_exists() -> None:
    assert _DOC_PATH.exists()


def test_every_alert_is_referenced_in_doc() -> None:
    payload = yaml.safe_load(_ALERTS_PATH.read_text(encoding="utf-8"))
    doc_text = _DOC_PATH.read_text(encoding="utf-8")
    missing = []
    for group in payload.get("groups", []):
        for rule in group.get("rules", []):
            alert_name = rule["alert"]
            if f"`{alert_name}`" not in doc_text:
                missing.append(alert_name)
    assert missing == [], f"alerts not referenced in doc: {missing}"


def test_every_runtime_counter_metric_is_documented() -> None:
    from qts.observability.metrics import RuntimeCounterMetric

    doc_text = _DOC_PATH.read_text(encoding="utf-8")
    missing = [
        member.value for member in RuntimeCounterMetric if f"`{member.value}`" not in doc_text
    ]
    assert missing == [], f"counter metrics not documented: {missing}"


def test_every_runtime_latency_metric_is_documented() -> None:
    from qts.observability.metrics import RuntimeLatencyMetric

    doc_text = _DOC_PATH.read_text(encoding="utf-8")
    missing = [
        member.value for member in RuntimeLatencyMetric if f"`{member.value}`" not in doc_text
    ]
    assert missing == [], f"latency metrics not documented: {missing}"
