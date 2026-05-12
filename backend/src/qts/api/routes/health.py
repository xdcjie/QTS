"""Health API routes."""

from __future__ import annotations

from fastapi import APIRouter

from qts.application.services import HealthService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Perform health."""
    status = HealthService().status()
    return {"status": status.status}


__all__ = ["router"]
