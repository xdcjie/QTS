"""Operational runtime and kill-switch API routes."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, model_validator

from qts.api.mappers import map_kill_switch_state_dto, map_runtime_state_dto
from qts.api.services import CommandIdempotencyStore
from qts.application.dto import KillSwitchCommandDTO
from qts.application.services import OperationsService

router = APIRouter(prefix="/operations")
_idempotency = CommandIdempotencyStore()
_operations = OperationsService()


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
        """Perform validate_scope."""
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


def _require_operator(operator: str | None) -> None:
    """Perform _require_operator."""
    if operator is None or not operator.strip():
        raise HTTPException(status_code=403, detail="operator permission required")


@router.post("/runtime/pause", response_model=RuntimeCommandResponse)
def pause_runtime(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponse:
    """Pause runtime execution for all strategies and data actors."""
    _require_operator(operator)

    def command() -> RuntimeCommandResponse:
        """Perform command."""
        state = _operations.pause_runtime()
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponse(**payload)

    if idempotency_key is None:
        return command()
    return _idempotency.run(idempotency_key, command)


@router.post("/runtime/resume", response_model=RuntimeCommandResponse)
def resume_runtime(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponse:
    """Resume runtime execution after an operator pause."""
    _require_operator(operator)

    def command() -> RuntimeCommandResponse:
        """Perform command."""
        state = _operations.resume_runtime()
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponse(**payload)

    if idempotency_key is None:
        return command()
    return _idempotency.run(idempotency_key, command)


@router.post("/kill-switches", response_model=KillSwitchResponse)
def activate_kill_switch(
    command: KillSwitchCommand,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> KillSwitchResponse:
    """Activate or refresh a kill-switch for a runtime scope."""
    _require_operator(operator)
    state = _operations.activate_kill_switch(
        KillSwitchCommandDTO(
            scope=command.scope.value,
            scope_id=command.scope_id,
            reason=command.reason,
        )
    )
    payload = map_kill_switch_state_dto(state)
    return KillSwitchResponse(**payload)


__all__ = ["router"]
