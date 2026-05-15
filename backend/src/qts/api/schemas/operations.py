"""Operational API schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, model_validator


class RuntimeCommandResponseSchema(BaseModel):
    """Payload for runtime pause/resume commands."""

    state: str


class RuntimeCommandResultResponseSchema(BaseModel):
    """Payload for auditable runtime command results."""

    command_id: str
    idempotency_key: str
    status: str
    evidence: dict[str, object]
    failure_reason: str | None = None
    reason_code: str | None = None


class KillSwitchScopeSchema(StrEnum):
    """Kill-switch scoping model."""

    GLOBAL = "global"
    ACCOUNT = "account"
    STRATEGY = "strategy"
    INSTRUMENT = "instrument"


class KillSwitchCommandSchema(BaseModel):
    """Kill-switch mutation command."""

    scope: KillSwitchScopeSchema
    scope_id: str | None = None
    reason: str

    @model_validator(mode="after")
    def validate_scope(self) -> KillSwitchCommandSchema:
        """Validate kill-switch command scope constraints."""
        if not self.reason.strip():
            raise ValueError("reason must not be empty")
        if self.scope is not KillSwitchScopeSchema.GLOBAL and (
            self.scope_id is None or not self.scope_id.strip()
        ):
            raise ValueError("scope_id is required for non-global scope")
        return self


class KillSwitchResponseSchema(BaseModel):
    """Kill-switch current state response."""

    scope: str
    scope_id: str | None
    active: bool
    reason: str


RuntimeCommandResponse = RuntimeCommandResponseSchema
RuntimeCommandResultResponse = RuntimeCommandResultResponseSchema
KillSwitchCommand = KillSwitchCommandSchema
KillSwitchResponse = KillSwitchResponseSchema


__all__ = [
    "RuntimeCommandResponse",
    "RuntimeCommandResponseSchema",
    "RuntimeCommandResultResponse",
    "RuntimeCommandResultResponseSchema",
    "KillSwitchScopeSchema",
    "KillSwitchCommand",
    "KillSwitchCommandSchema",
    "KillSwitchResponse",
    "KillSwitchResponseSchema",
]
