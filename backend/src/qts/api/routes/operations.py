"""Operational runtime and kill-switch API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from qts.api.mappers import map_kill_switch_state_dto, map_runtime_state_dto
from qts.api.schemas.operations import (
    KillSwitchCommandSchema,
    KillSwitchResponseSchema,
    RuntimeCommandResponseSchema,
)
from qts.api.services import CommandIdempotencyStore
from qts.application.dto import KillSwitchCommandDTO
from qts.application.services import OperationsService

router = APIRouter(prefix="/operations")
_idempotency = CommandIdempotencyStore()
_operations = OperationsService()


def _require_operator(operator: str | None) -> None:
    """Validate X-QTS-Operator header is present."""
    if operator is None or not operator.strip():
        raise HTTPException(status_code=403, detail="operator permission required")


@router.post("/runtime/pause", response_model=RuntimeCommandResponseSchema)
def pause_runtime(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Pause runtime execution for all strategies and data actors."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute pause command and return updated runtime state."""
        state = _operations.pause_runtime()
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return _idempotency.run(idempotency_key, command)


@router.post("/runtime/resume", response_model=RuntimeCommandResponseSchema)
def resume_runtime(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Resume runtime execution after an operator pause."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute resume command and return updated runtime state."""
        state = _operations.resume_runtime()
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return _idempotency.run(idempotency_key, command)


@router.post("/kill-switches", response_model=KillSwitchResponseSchema)
def activate_kill_switch(
    command: KillSwitchCommandSchema,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> KillSwitchResponseSchema:
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
    return KillSwitchResponseSchema(**payload)


__all__ = ["router"]
