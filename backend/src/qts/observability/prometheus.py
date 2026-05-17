"""Prometheus text-format exporter for the runtime MetricsRegistry.

Owner of the wire-format translation between the internal flat metric dict
maintained by ``MetricsRegistry`` and the canonical Prometheus
``text/plain; version=0.0.4`` representation.

This module deliberately avoids the ``prometheus_client`` dependency: the
runtime owns the canonical counter/gauge state, and a thin renderer keeps
the dependency surface small while still letting an external scraper pull
the same data through ``/metrics``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from qts.observability.metrics import MetricsRegistry, RuntimeCounterMetric, RuntimeLatencyMetric

PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"

_COUNTER_NAMES: frozenset[str] = frozenset(member.value for member in RuntimeCounterMetric)
_LATENCY_NAMES: frozenset[str] = frozenset(member.value for member in RuntimeLatencyMetric)

_METRIC_HELP: dict[str, str] = {
    RuntimeCounterMetric.MARKET_DATA_EVENTS_TOTAL.value: "Total market data events ingested.",
    RuntimeCounterMetric.MARKET_DATA_STALE_TOTAL.value: "Total market data staleness incidents.",
    RuntimeCounterMetric.MARKET_DATA_SUBSCRIPTION_FAILURES_TOTAL.value: (
        "Total market data subscription failures by reason."
    ),
    RuntimeCounterMetric.STRATEGY_INTENTS_TOTAL.value: "Total strategy intents emitted.",
    RuntimeCounterMetric.SIGNAL_CONFLICTS_TOTAL.value: "Total signal conflicts.",
    RuntimeCounterMetric.RISK_REJECTIONS_TOTAL.value: "Total risk rejections by reason.",
    RuntimeCounterMetric.ORDERS_SUBMITTED_TOTAL.value: "Total orders submitted to brokers.",
    RuntimeCounterMetric.BROKER_REJECTIONS_TOTAL.value: "Total broker rejections by reason.",
    RuntimeCounterMetric.FILLS_TOTAL.value: "Total fills applied to accounts.",
    RuntimeCounterMetric.RECONCILIATION_DRIFTS_TOTAL.value: "Total reconciliation drifts detected.",
    RuntimeCounterMetric.KILL_SWITCH_ACTIVATIONS_TOTAL.value: "Total kill-switch activations.",
    RuntimeCounterMetric.RUNTIME_RECOVERY_BLOCKS_TOTAL.value: (
        "Total runtime recovery blocks by reason."
    ),
    RuntimeLatencyMetric.MARKET_DATA_INGEST_LATENCY.value: "Latest market-data ingest latency.",
    RuntimeLatencyMetric.STRATEGY_EVAL_LATENCY.value: "Latest strategy evaluation latency.",
    RuntimeLatencyMetric.SIGNAL_AGGREGATION_LATENCY.value: "Latest signal aggregation latency.",
    RuntimeLatencyMetric.RISK_EVAL_LATENCY.value: "Latest risk evaluation latency.",
    RuntimeLatencyMetric.ORDER_MANAGER_LATENCY.value: "Latest order-manager latency.",
    RuntimeLatencyMetric.BROKER_SUBMIT_LATENCY.value: "Latest broker submission latency.",
    RuntimeLatencyMetric.BROKER_ACK_LATENCY.value: "Latest broker acknowledgement latency.",
    RuntimeLatencyMetric.FILL_TO_ACCOUNT_APPLY_LATENCY.value: (
        "Latest fill-to-account application latency."
    ),
}


def render_prometheus_text(registry: MetricsRegistry) -> str:
    """Return the registry's snapshot in Prometheus text format."""
    snapshot = registry.snapshot()
    grouped: dict[str, list[tuple[str | None, int | float]]] = {}
    for key, value in snapshot.items():
        name, tags_text = _parse_key(key)
        grouped.setdefault(name, []).append((tags_text, value))

    lines: list[str] = []
    for raw_name in sorted(grouped):
        prom_name = _to_prometheus_name(raw_name)
        metric_type = _resolve_type(raw_name)
        help_text = _METRIC_HELP.get(raw_name, f"Metric: {raw_name}")
        lines.append(f"# HELP {prom_name} {help_text}")
        lines.append(f"# TYPE {prom_name} {metric_type}")
        for tags_text, value in grouped[raw_name]:
            labels = _render_labels(tags_text)
            lines.append(f"{prom_name}{labels} {value}")
    return "\n".join(lines) + ("\n" if lines else "")


def _parse_key(key: str) -> tuple[str, str | None]:
    if key.endswith("}") and "{" in key:
        name, _, rest = key.partition("{")
        return name, rest[:-1]
    return key, None


def _to_prometheus_name(raw_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", raw_name)


def _resolve_type(raw_name: str) -> str:
    if raw_name in _COUNTER_NAMES or raw_name.endswith("_total"):
        return "counter"
    if raw_name in _LATENCY_NAMES or raw_name.endswith("_latency"):
        return "gauge"  # latest-observation gauge until per-bucket histograms ship
    return "gauge"


def _render_labels(tags_text: str | None) -> str:
    if not tags_text:
        return ""
    pairs = _parse_tags(tags_text)
    if not pairs:
        return ""
    rendered = ",".join(f'{key}="{value}"' for key, value in pairs)
    return "{" + rendered + "}"


def _parse_tags(tags_text: str) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for fragment in tags_text.split(","):
        if "=" not in fragment:
            continue
        key, _, value = fragment.partition("=")
        pairs.append((key.strip(), value.strip()))
    return tuple(sorted(pairs))


def metrics_response_body(snapshot: Mapping[str, int | float]) -> str:
    """Render a pre-collected metric snapshot directly."""
    placeholder = MetricsRegistry()
    placeholder._values = dict(snapshot)
    return render_prometheus_text(placeholder)


__all__ = [
    "PROMETHEUS_CONTENT_TYPE",
    "metrics_response_body",
    "render_prometheus_text",
]
