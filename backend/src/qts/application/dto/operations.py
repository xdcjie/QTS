"""Operational application DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeStateDTO:
    """Stable runtime state response."""

    state: str


@dataclass(frozen=True, slots=True)
class KillSwitchCommandDTO:
    """Stable kill-switch activation request."""

    scope: str
    reason: str
    scope_id: str | None = None

    def __post_init__(self) -> None:
        if not self.scope.strip():
            raise ValueError("scope must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")
        if self.scope != "global" and (self.scope_id is None or not self.scope_id.strip()):
            raise ValueError("scope_id is required for non-global scope")


@dataclass(frozen=True, slots=True)
class KillSwitchStateDTO:
    """Stable kill-switch state response."""

    scope: str
    active: bool
    reason: str
    scope_id: str | None = None


__all__ = ["KillSwitchCommandDTO", "KillSwitchStateDTO", "RuntimeStateDTO"]
