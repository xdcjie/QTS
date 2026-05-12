"""Operational API schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, model_validator


class RuntimeCommandResponse(BaseModel):
    """Payload for runtime pause/resume commands."""

    state: str


class KillSwitchScopeSchema(StrEnum):
    """Kill-switch scoping model."""

    GLOBAL = "global"
    ACCOUNT = "account"
    STRATEGY = "strategy"
    INSTRUMENT = "instrument"


class KillSwitchCommand(BaseModel):
    """Kill-switch mutation command."""

    scope: KillSwitchScopeSchema
    scope_id: str | None = None
    reason: str

    @model_validator(mode="after")
    def validate_scope(self) -> KillSwitchCommand:
        """Validate kill-switch command scope constraints."""
        if not self.reason.strip():
            raise ValueError("reason must not be empty")
        if self.scope is not KillSwitchScopeSchema.GLOBAL and (
            self.scope_id is None or not self.scope_id.strip()
        ):
            raise ValueError("scope_id is required for non-global scope")
        return self


class KillSwitchResponse(BaseModel):
    """Kill-switch current state response."""

    scope: str
    scope_id: str | None
    active: bool
    reason: str


__all__ = [
    "RuntimeCommandResponse",
    "KillSwitchScopeSchema",
    "KillSwitchCommand",
    "KillSwitchResponse",
]
