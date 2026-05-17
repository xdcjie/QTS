"""Anchor: configs/alerts/qts_alerts.yaml is schema-valid and metric-grounded.

Domain fact: alerts are durable specifications; every rule references a
metric the runtime actually populates. A rule with a metric typo is dead
infrastructure.

Owner: ``configs/alerts/qts_alerts.yaml``.

Forbidden shortcut: alerts referencing metrics that aren't recorded by
``MetricsRegistry``; missing severity / runbook annotation.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from qts.observability.metrics import RuntimeCounterMetric, RuntimeLatencyMetric

_ALERTS_PATH = Path("configs/alerts/qts_alerts.yaml")
_EXPECTED_ALERT_COUNT = 8
_REQUIRED_LABELS = {"severity"}
_REQUIRED_ANNOTATIONS = {"summary", "description", "runbook_url"}
_ALLOWED_SEVERITIES = {"page", "warn", "info"}
_KNOWN_METRIC_NAMES: frozenset[str] = frozenset(
    [member.value for member in RuntimeCounterMetric]
    + [member.value for member in RuntimeLatencyMetric]
)
_METRIC_NAME_PATTERN = re.compile(r"[a-z][a-z0-9_]*")


def _all_rules() -> list[dict[str, object]]:
    payload = yaml.safe_load(_ALERTS_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    groups = payload.get("groups", [])
    assert isinstance(groups, list)
    rules: list[dict[str, object]] = []
    for group in groups:
        assert isinstance(group, dict)
        for rule in group.get("rules", []):
            assert isinstance(rule, dict)
            rules.append(rule)
    return rules


def test_alert_rules_file_exists_and_parses() -> None:
    assert _ALERTS_PATH.exists()
    rules = _all_rules()
    assert len(rules) == _EXPECTED_ALERT_COUNT


def test_every_alert_has_required_fields() -> None:
    for rule in _all_rules():
        alert_name = rule.get("alert")
        assert isinstance(alert_name, str), rule
        assert "expr" in rule, alert_name
        assert "for" in rule, alert_name
        labels = rule.get("labels", {})
        assert isinstance(labels, dict)
        assert _REQUIRED_LABELS.issubset(labels.keys()), alert_name
        assert labels["severity"] in _ALLOWED_SEVERITIES, alert_name
        annotations = rule.get("annotations", {})
        assert isinstance(annotations, dict)
        assert _REQUIRED_ANNOTATIONS.issubset(annotations.keys()), alert_name
        assert annotations["runbook_url"].startswith("docs/"), alert_name


def test_every_alert_references_a_known_metric() -> None:
    for rule in _all_rules():
        expr = rule["expr"]
        assert isinstance(expr, str)
        # The Prometheus expr starts with a metric name (possibly wrapped in
        # rate(...) / increase(...)). Strip those wrappers and verify the
        # innermost identifier is a known metric.
        unwrapped = re.sub(r"^(?:rate|increase)\(", "", expr)
        unwrapped = unwrapped.split("[")[0].split(" ")[0].strip()
        unwrapped = unwrapped.lstrip("(").rstrip(")")
        assert unwrapped in _KNOWN_METRIC_NAMES, (
            f"alert {rule['alert']} references unknown metric {unwrapped!r}; "
            f"add it to RuntimeCounterMetric/RuntimeLatencyMetric or fix the alert."
        )
