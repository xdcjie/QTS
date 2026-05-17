"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from qts.api.routes import (
    accounts_router,
    backtests_router,
    health_router,
    operations_router,
    orders_router,
    strategies_router,
)
from qts.api.security import ApiSecurityMiddleware, default_auth_backend
from qts.api.websocket import events_router


def create_app() -> FastAPI:
    """Perform create_app."""
    app = FastAPI(title="Quant Trading System")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-QTS-Operator"],
    )
    app.add_middleware(ApiSecurityMiddleware, auth_backend=default_auth_backend())
    app.include_router(health_router)
    app.include_router(backtests_router)
    app.include_router(strategies_router)
    app.include_router(accounts_router)
    app.include_router(orders_router)
    app.include_router(operations_router)
    app.include_router(events_router)
    return app


__all__ = ["create_app"]
