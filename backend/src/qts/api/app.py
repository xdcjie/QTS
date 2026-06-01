"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from qts.api.services import CommandIdempotencyStore
from qts.api.websocket import events_router
from qts.application.services import OperationsService
from qts.observability.metrics import MetricsRegistry
from qts.observability.prometheus import PROMETHEUS_CONTENT_TYPE, render_prometheus_text
from qts.runtime.errors import RuntimeCommandNotBound


def create_app(
    *,
    metrics: MetricsRegistry | None = None,
    operations_service: OperationsService | None = None,
) -> FastAPI:
    """Build the FastAPI app with CORS, security, metrics, and all routers.

    ``operations_service`` is bound to ``app.state`` so operator control-plane
    routes resolve it through dependency injection rather than a module global;
    production wiring passes a runtime-bound service, and tests may override it.
    """
    app = FastAPI(title="Quant Trading System")
    metrics_registry: MetricsRegistry = metrics or MetricsRegistry()
    app.state.metrics = metrics_registry
    app.state.operations_service = operations_service or OperationsService()
    app.state.command_idempotency = CommandIdempotencyStore()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-QTS-Operator",
            "X-QTS-Runtime-Instance-Id",
        ],
    )
    app.add_middleware(ApiSecurityMiddleware, auth_backend=default_auth_backend())

    @app.exception_handler(RuntimeCommandNotBound)
    def _runtime_session_not_bound(_request: Request, exc: RuntimeCommandNotBound) -> JSONResponse:
        """Map an unbound operator command to 503 without faking success."""
        return JSONResponse(
            status_code=503,
            content={"reason_code": "RUNTIME_SESSION_NOT_BOUND", "detail": str(exc)},
        )

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
