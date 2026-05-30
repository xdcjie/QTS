"""Health application service."""

from __future__ import annotations

from qts.application.dto import HealthStatusDTO


class HealthService:
    """Returns platform health without exposing internals."""

    def status(self) -> HealthStatusDTO:
        """Return an ok platform health status DTO."""
        return HealthStatusDTO(status="ok")


__all__ = ["HealthService"]
