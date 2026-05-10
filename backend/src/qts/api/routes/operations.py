"""Operational runtime and kill-switch API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from qts.api.services import CommandIdempotencyStore
from qts.risk.kill_switch import KillSwitchRegistry, KillSwitchScope, KillSwitchScopeType
from qts.runtime.live import LiveRuntimeState

router = APIRouter(prefix="/operations")
_idempotency = CommandIdempotencyStore()
_kill_switches = KillSwitchRegistry()
_runtime_state = LiveRuntimeState.RUNNING


class RuntimeCommandResponse(BaseModel):
    state: str


class KillSwitchCommand(BaseModel):
    scope: KillSwitchScopeType
    scope_id: str | None = None
    reason: str


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
        global _runtime_state
        _runtime_state = LiveRuntimeState.PAUSED
        return RuntimeCommandResponse(state=_runtime_state.value)

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
        global _runtime_state
        _runtime_state = LiveRuntimeState.RUNNING
        return RuntimeCommandResponse(state=_runtime_state.value)

    if idempotency_key is None:
        return command()
    return _idempotency.run(idempotency_key, command)


@router.post("/kill-switches", response_model=KillSwitchResponse)
def activate_kill_switch(
    command: KillSwitchCommand,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> KillSwitchResponse:
    _require_operator(operator)
    scope = _scope_from_command(command)
    state = _kill_switches.activate(scope, reason=command.reason)
    return KillSwitchResponse(
        scope=state.scope.scope_type.value,
        scope_id=state.scope.scope_id,
        active=state.active,
        reason=state.reason,
    )


def _scope_from_command(command: KillSwitchCommand) -> KillSwitchScope:
    if command.scope is KillSwitchScopeType.GLOBAL:
        return KillSwitchScope.global_scope()
    if command.scope_id is None or not command.scope_id.strip():
        raise HTTPException(status_code=422, detail="scope_id is required for non-global scope")
    return KillSwitchScope(command.scope, command.scope_id)


__all__ = ["router"]
