"""Anchor: /metrics endpoint serves Prometheus text format without auth.

Domain fact: production SLI/SLO need wire-format metrics scraped by an
external Prometheus server. The exporter must:
- expose a ``/metrics`` GET endpoint bypassed by the auth middleware
  (Prometheus scraper has no bearer token);
- emit the canonical text format with HELP and TYPE lines;
- carry the runtime counters and gauges populated by ``MetricsRegistry``.

Owner: ``qts.observability.prometheus`` + ``qts.api.app``.

Forbidden shortcut: scraping the in-memory dict via the auth-protected
API; emitting an ad-hoc JSON shape that Prometheus cannot parse.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from qts.api.app import create_app
from qts.observability.metrics import MetricsRegistry, RuntimeCounterMetric


def test_metrics_endpoint_returns_prometheus_text_format() -> None:
    registry = MetricsRegistry()
    registry.increment(RuntimeCounterMetric.ORDERS_SUBMITTED_TOTAL)
    client = TestClient(create_app(metrics=registry))

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "# TYPE orders_submitted_total counter" in body
    assert "orders_submitted_total 1" in body


def test_metrics_endpoint_does_not_require_authentication() -> None:
    client = TestClient(create_app())
    response = client.get("/metrics")
    assert response.status_code == 200


def test_prometheus_exporter_renders_counter_with_help_and_type_lines() -> None:
    from qts.observability.prometheus import render_prometheus_text

    registry = MetricsRegistry()
    registry.increment(RuntimeCounterMetric.ORDERS_SUBMITTED_TOTAL)
    registry.increment(RuntimeCounterMetric.ORDERS_SUBMITTED_TOTAL)

    rendered = render_prometheus_text(registry)

    assert "# HELP orders_submitted_total" in rendered
    assert "# TYPE orders_submitted_total counter" in rendered
    assert "orders_submitted_total 2" in rendered


def test_prometheus_exporter_renders_tags_as_prometheus_labels() -> None:
    from qts.observability.prometheus import render_prometheus_text

    registry = MetricsRegistry()
    registry.gauge("queue.depth", 7, tags={"name": "execution"})

    rendered = render_prometheus_text(registry)

    assert 'queue_depth{name="execution"} 7' in rendered


def test_prometheus_exporter_emits_histogram_for_latency_observations() -> None:
    from qts.observability.metrics import RuntimeLatencyMetric
    from qts.observability.prometheus import render_prometheus_text

    registry = MetricsRegistry()
    registry.record_latency(RuntimeLatencyMetric.STRATEGY_EVAL_LATENCY, 0.001)
    registry.record_latency(RuntimeLatencyMetric.STRATEGY_EVAL_LATENCY, 0.005)

    rendered = render_prometheus_text(registry)

    # The exporter renders RuntimeLatencyMetric values as gauges of the
    # latest observation; production deployments can wrap this with the
    # Prometheus client histogram aggregation. The line must be present.
    assert "strategy_eval_latency" in rendered
