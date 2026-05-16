"""API mapping layer between schemas and application DTOs."""

from __future__ import annotations

from typing import Any

from qts.api.schemas.backtest_schema import BacktestRequestSchema, BacktestRunSchema
from qts.application.dto.backtest import BacktestRequestDTO, BacktestRunDTO
from qts.application.dto.operations import (
    KillSwitchStateDTO,
    OperatorAlertDTO,
    OperatorDashboardStatusDTO,
    OperatorStatusFieldDTO,
    RuntimeCommandResultDTO,
    RuntimeStateDTO,
)


def map_backtest_request_schema(request: BacktestRequestSchema) -> BacktestRequestDTO:
    """Map API input schema into an application DTO."""

    return BacktestRequestDTO(strategy_name=request.strategy_name)


def map_backtest_run_dto(run: BacktestRunDTO) -> BacktestRunSchema:
    """Map application output DTO into API response schema."""

    return BacktestRunSchema(run_id=run.run_id, strategy_name=run.strategy_name, status=run.status)


def map_runtime_state_dto(state: RuntimeStateDTO) -> dict[str, Any]:
    """Map runtime state DTO into response payload."""

    return {"state": state.state}


def map_runtime_command_result_dto(result: RuntimeCommandResultDTO) -> dict[str, Any]:
    """Map runtime command result DTO into response payload."""

    return {
        "command_id": result.command_id,
        "idempotency_key": result.idempotency_key,
        "status": result.status,
        "evidence": dict(result.evidence),
        "failure_reason": result.failure_reason,
        "reason_code": result.reason_code,
    }


def map_kill_switch_state_dto(state: KillSwitchStateDTO) -> dict[str, Any]:
    """Map kill-switch state DTO into response payload."""

    return {
        "scope": state.scope,
        "scope_id": state.scope_id,
        "active": state.active,
        "reason": state.reason,
    }


def map_operator_dashboard_status_dto(status: OperatorDashboardStatusDTO) -> dict[str, Any]:
    """Map operator dashboard status DTO into response payload."""

    return {
        **{name: _map_operator_status_field(field) for name, field in status.fields.items()},
        "alerts": [_map_operator_alert(alert) for alert in status.alerts],
    }


def _map_operator_status_field(field: OperatorStatusFieldDTO) -> dict[str, Any]:
    return {
        "value": _map_operator_value(field.value),
        "timestamp": field.timestamp.isoformat(),
    }


def _map_operator_alert(alert: OperatorAlertDTO) -> dict[str, str]:
    return {
        "code": alert.code,
        "severity": alert.severity,
        "message": alert.message,
        "timestamp": alert.timestamp.isoformat(),
    }


def _map_operator_value(value: object) -> object:
    if isinstance(value, tuple):
        return [_map_operator_value(item) for item in value]
    if isinstance(value, list):
        return [_map_operator_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _map_operator_value(item) for key, item in value.items()}
    return value


__all__ = [
    "map_backtest_request_schema",
    "map_backtest_run_dto",
    "map_kill_switch_state_dto",
    "map_operator_dashboard_status_dto",
    "map_runtime_command_result_dto",
    "map_runtime_state_dto",
]
