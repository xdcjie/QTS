"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from qts.api.auth_backend_factory import default_auth_backend
from qts.api.routes import (
    accounts_router,
    backtests_router,
    health_router,
    operations_router,
    orders_router,
    research_router,
    strategies_router,
)
from qts.api.security import ApiSecurityMiddleware
from qts.api.websocket import events_router
from qts.observability.metrics import MetricsRegistry
from qts.observability.prometheus import PROMETHEUS_CONTENT_TYPE, render_prometheus_text


def create_app(*, metrics: MetricsRegistry | None = None) -> FastAPI:
    """Perform create_app."""
    app = FastAPI(title="Quant Trading System")
    metrics_registry: MetricsRegistry = metrics or MetricsRegistry()
    app.state.metrics = metrics_registry
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-QTS-Operator"],
    )
    app.add_middleware(ApiSecurityMiddleware, auth_backend=default_auth_backend())

    @app.get("/metrics", include_in_schema=False)
    def _metrics_endpoint() -> Response:
        """Serve runtime metrics in Prometheus text format."""
        body = render_prometheus_text(metrics_registry)
        return Response(content=body, media_type=PROMETHEUS_CONTENT_TYPE)

    app.include_router(health_router)
    app.include_router(backtests_router)
    app.include_router(strategies_router)
    app.include_router(accounts_router)
    app.include_router(orders_router)
    app.include_router(research_router)
    app.include_router(operations_router)
    app.include_router(events_router)
    return app


__all__ = ["create_app"]
