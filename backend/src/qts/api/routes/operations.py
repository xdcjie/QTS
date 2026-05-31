"""Operational runtime and kill-switch API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from qts.api.mappers import (
    map_kill_switch_state_dto,
    map_operator_dashboard_status_dto,
    map_runtime_command_result_dto,
    map_runtime_state_dto,
)
from qts.api.schemas.operations import (
    KillSwitchCommandSchema,
    KillSwitchResponseSchema,
    RuntimeCommandResponseSchema,
    RuntimeCommandResultResponseSchema,
)
from qts.api.services import CommandIdempotencyStore
from qts.application.dto import KillSwitchCommandDTO
from qts.application.services import OperationsService

router = APIRouter(prefix="/operations")


def get_operations_service(request: Request) -> OperationsService:
    """Resolve the request-scoped OperationsService from application state.

    The service is bound in ``create_app`` (and overridable by tests via
    ``app.state``); routes never reach for a module-global instance, so the
    operational control plane can be wired to a real runtime at app construction.
    """
    service = getattr(request.app.state, "operations_service", None)
    if not isinstance(service, OperationsService):
        raise HTTPException(status_code=503, detail="operations service is not configured")
    return service


def get_command_idempotency(request: Request) -> CommandIdempotencyStore:
    """Resolve the request-scoped command idempotency store from application state."""
    store = getattr(request.app.state, "command_idempotency", None)
    if not isinstance(store, CommandIdempotencyStore):
        raise HTTPException(status_code=503, detail="command idempotency store is not configured")
    return store


OperationsServiceDep = Annotated[OperationsService, Depends(get_operations_service)]
CommandIdempotencyDep = Annotated[CommandIdempotencyStore, Depends(get_command_idempotency)]


def _require_operator(operator: str | None) -> None:
    """Validate X-QTS-Operator header is present."""
    if operator is None or not operator.strip():
        raise HTTPException(status_code=403, detail="operator permission required")


@router.get("/operator-status")
def operator_status(
    operations: OperationsServiceDep,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> dict[str, object]:
    """Return application-owned operator dashboard status."""

    _require_operator(operator)
    return map_operator_dashboard_status_dto(operations.operator_status())


@router.post("/runtime/start", response_model=RuntimeCommandResponseSchema)
def start_runtime(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Start runtime processing."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute start command and return updated runtime state."""
        assert operator is not None
        state = operations.start_runtime(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.start")


@router.post("/runtime/stop", response_model=RuntimeCommandResponseSchema)
def stop_runtime(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Stop runtime processing."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute stop command and return updated runtime state."""
        assert operator is not None
        state = operations.stop_runtime(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.stop")


@router.post("/runtime/pause", response_model=RuntimeCommandResponseSchema)
def pause_runtime(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Pause runtime execution for all strategies and data actors."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute pause command and return updated runtime state."""
        assert operator is not None
        state = operations.pause_runtime(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.pause")


@router.post("/runtime/resume", response_model=RuntimeCommandResponseSchema)
def resume_runtime(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Resume runtime execution after an operator pause."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute resume command and return updated runtime state."""
        assert operator is not None
        state = operations.resume_runtime(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.resume")


@router.post("/runtime/enter-observation", response_model=RuntimeCommandResponseSchema)
def enter_observation(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Enter observation mode while keeping runtime visibility."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute enter-observation command and return updated runtime state."""
        assert operator is not None
        state = operations.enter_observation(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.enter_observation")


@router.post("/runtime/exit-observation", response_model=RuntimeCommandResponseSchema)
def exit_observation(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResponseSchema:
    """Exit observation mode after operator approval."""

    _require_operator(operator)

    def command() -> RuntimeCommandResponseSchema:
        """Execute exit-observation command and return updated runtime state."""
        assert operator is not None
        state = operations.exit_observation(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_state_dto(state)
        return RuntimeCommandResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.exit_observation")


@router.post("/runtime/reconcile", response_model=RuntimeCommandResultResponseSchema)
def reconcile_runtime(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResultResponseSchema:
    """Request runtime reconciliation through the operational command boundary."""

    _require_operator(operator)

    def command() -> RuntimeCommandResultResponseSchema:
        """Execute reconcile command and return audit evidence."""
        assert operator is not None
        result = operations.reconcile_runtime(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_command_result_dto(result)
        return RuntimeCommandResultResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.reconcile")


@router.post("/runtime/snapshot", response_model=RuntimeCommandResultResponseSchema)
def snapshot_runtime(
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> RuntimeCommandResultResponseSchema:
    """Request a runtime snapshot through the operational command boundary."""

    _require_operator(operator)

    def command() -> RuntimeCommandResultResponseSchema:
        """Execute snapshot command and return audit evidence."""
        assert operator is not None
        result = operations.snapshot_runtime(
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_runtime_command_result_dto(result)
        return RuntimeCommandResultResponseSchema(**payload)

    if idempotency_key is None:
        return command()
    return idempotency.run(idempotency_key, command, scope="runtime.snapshot")


@router.post("/kill-switches", response_model=KillSwitchResponseSchema)
def activate_kill_switch(
    command: KillSwitchCommandSchema,
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> KillSwitchResponseSchema:
    """Activate or refresh a kill-switch for a runtime scope."""

    _require_operator(operator)
    assert operator is not None

    def runtime_command() -> KillSwitchResponseSchema:
        """Execute kill-switch command and return updated switch state."""
        state = operations.activate_kill_switch(
            KillSwitchCommandDTO(
                scope=command.scope.value,
                scope_id=command.scope_id,
                reason=command.reason,
            ),
            operator_id=operator.strip(),
            idempotency_key=idempotency_key,
        )
        payload = map_kill_switch_state_dto(state)
        return KillSwitchResponseSchema(**payload)

    if idempotency_key is None:
        return runtime_command()
    return idempotency.run(idempotency_key, runtime_command, scope="runtime.kill_switch")


@router.post("/kill-switches/deactivate", response_model=KillSwitchResponseSchema)
def deactivate_kill_switch(
    command: KillSwitchCommandSchema,
    operations: OperationsServiceDep,
    idempotency: CommandIdempotencyDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    operator: Annotated[str | None, Header(alias="X-QTS-Operator")] = None,
) -> KillSwitchResponseSchema:
    """Deactivate or refresh an inactive kill-switch state for a runtime scope."""

    _require_operator(operator)
    assert operator is not None

    def runtime_command() -> KillSwitchResponseSchema:
        """Execute kill-switch deactivation and return updated switch state."""
        state = operations.deactivate_kill_switch(
            KillSwitchCommandDTO(
                scope=command.scope.value,
                scope_id=command.scope_id,
                reason=command.reason,
            ),
            operator_id=operator.strip(),
            authorization_scope="runtime:safety:write",
            idempotency_key=idempotency_key,
        )
        payload = map_kill_switch_state_dto(state)
        return KillSwitchResponseSchema(**payload)

    if idempotency_key is None:
        return runtime_command()
    return idempotency.run(
        idempotency_key,
        runtime_command,
        scope="runtime.kill_switch_deactivate",
    )


__all__ = ["get_command_idempotency", "get_operations_service", "router"]
