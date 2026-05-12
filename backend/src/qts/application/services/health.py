"""Health application service."""

from __future__ import annotations

from qts.application.dto import HealthStatusDTO


class HealthService:
    """Returns platform health without exposing internals."""

    def status(self) -> HealthStatusDTO:
        """Perform status."""
        return HealthStatusDTO(status="ok")


__all__ = ["HealthService"]
