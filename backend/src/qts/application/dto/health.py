"""Application health DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HealthStatusDTO:
    """Stable health status response."""

    status: str


__all__ = ["HealthStatusDTO"]
