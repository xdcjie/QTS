"""Operational application DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RuntimeStateDTO:
    """Stable runtime state response."""

    state: str


@dataclass(frozen=True, slots=True)
class RuntimeCommandResultDTO:
    """Stable runtime command result for API and CLI callers."""

    command_id: str
    idempotency_key: str
    status: str
    evidence: Mapping[str, object] = field(default_factory=dict)
    failure_reason: str | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        """Normalize evidence into an immutable DTO payload."""
        if not self.command_id.strip():
            raise ValueError("command_id must not be empty")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        if not self.status.strip():
            raise ValueError("status must not be empty")
        object.__setattr__(self, "evidence", dict(self.evidence))


@dataclass(frozen=True, slots=True)
class KillSwitchCommandDTO:
    """Stable kill-switch activation request."""

    scope: str
    reason: str
    scope_id: str | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
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


__all__ = [
    "KillSwitchCommandDTO",
    "KillSwitchStateDTO",
    "RuntimeCommandResultDTO",
    "RuntimeStateDTO",
]
