"""Operational runtime and kill-switch API routes."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, model_validator

from qts.api.services import CommandIdempotencyStore
from qts.application.dto import KillSwitchCommandDTO
from qts.application.services import OperationsService

router = APIRouter(prefix="/operations")
_idempotency = CommandIdempotencyStore()
_operations = OperationsService()


class RuntimeCommandResponse(BaseModel):
    state: str


class KillSwitchScopeSchema(StrEnum):
    GLOBAL = "global"
    ACCOUNT = "account"
    STRATEGY = "strategy"
    INSTRUMENT = "instrument"


class KillSwitchCommand(BaseModel):
    scope: KillSwitchScopeSchema
    scope_id: str | None = None
    reason: str

    @model_validator(mode="after")
    def validate_scope(self) -> KillSwitchCommand:
        if not self.reason.strip():
            raise ValueError("reason must not be empty")
        if self.scope is not KillSwitchScopeSchema.GLOBAL and (
            self.scope_id is None or not self.scope_id.strip()
        ):
            raise ValueError("scope_id is required for non-global scope")
        return self


class KillSwitchResponse(BaseModel):
    scope: str
    scope_id: str | None
    active: bool
    reason: str


def _require_operator(operator: str | None) -> None:
    if operator is None or not operator.strip():
        raise HTTPException(status_code=403, detail="operator permission required")


@router.post("/runtime/pause", response_model=RuntimeCommandResponse)
def pause_runtime(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponse:
    _require_operator(operator)

    def command() -> RuntimeCommandResponse:
        state = _operations.pause_runtime()
        return RuntimeCommandResponse(state=state.state)

    if idempotency_key is None:
        return command()
    return _idempotency.run(idempotency_key, command)


@router.post("/runtime/resume", response_model=RuntimeCommandResponse)
def resume_runtime(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponse:
    _require_operator(operator)

    def command() -> RuntimeCommandResponse:
        state = _operations.resume_runtime()
        return RuntimeCommandResponse(state=state.state)

    if idempotency_key is None:
        return command()
    return _idempotency.run(idempotency_key, command)


@router.post("/kill-switches", response_model=KillSwitchResponse)
def activate_kill_switch(
    command: KillSwitchCommand,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> KillSwitchResponse:
    _require_operator(operator)
    state = _operations.activate_kill_switch(
        KillSwitchCommandDTO(
            scope=command.scope.value,
            scope_id=command.scope_id,
            reason=command.reason,
        )
    )
    return KillSwitchResponse(
        scope=state.scope,
        scope_id=state.scope_id,
        active=state.active,
        reason=state.reason,
    )


__all__ = ["router"]
