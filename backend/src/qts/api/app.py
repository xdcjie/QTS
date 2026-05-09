"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from qts.api.routes import backtests_router, health_router
from qts.api.websocket import events_router


def create_app() -> FastAPI:
    app = FastAPI(title="Quant Trading System")
    app.include_router(health_router)
    app.include_router(backtests_router)
    app.include_router(events_router)
    return app


__all__ = ["create_app"]
