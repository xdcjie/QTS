"""Health API routes.

Three differentiated probes with explicit semantics:

- ``GET /health/liveness`` — process is responsive (smoke); restart the pod
  if this fails.
- ``GET /health/readiness`` — runtime is in a ready state suitable to serve
  traffic / submit orders; remove from load balancer if this fails but do
  not restart.
- ``GET /health/startup`` — initial boot completed; grace period for slow
  starts. Returns 200 in backtest/test modes which have no startup gate.
All four bypass ``ApiSecurityMiddleware`` (whitelisted in the middleware
dispatch) so Prometheus / k8s probes do not require bearer tokens.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from qts.application.services import HealthService

router = APIRouter()


@router.get("/health/liveness")
def liveness() -> dict[str, str]:
    """Return liveness — true if the process is responsive."""
    return {"status": "live"}


@router.get("/health/readiness")
def readiness(response: Response) -> dict[str, object]:
    """Return readiness — true if the runtime is ready to serve traffic."""
    status = HealthService().status()
    ready = status.status == "ok"
    if not ready:
        response.status_code = 503
    return {"ready": ready, "status": status.status}


@router.get("/health/startup")
def startup() -> dict[str, str]:
    """Return startup completion — true once initial boot has finished."""
    return {"status": "started"}


__all__ = ["router"]
