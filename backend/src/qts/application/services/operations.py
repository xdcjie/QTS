"""Operational application service."""

from __future__ import annotations

from qts.application.dto import (
    KillSwitchCommandDTO,
    KillSwitchStateDTO,
    OperatorDashboardStatusDTO,
    RuntimeCommandResultDTO,
    RuntimeStateDTO,
)
from qts.application.services.kill_switch_commands import KillSwitchCommandService
from qts.application.services.operations_command_handler import OperationsCommandHandler
from qts.application.services.operations_command_router import OperationsCommandRouter
from qts.application.services.operator_dashboard import OperatorDashboardService
from qts.application.services.runtime_lifecycle import RuntimeLifecycleService
from qts.risk.kill_switch import KillSwitchRegistry
from qts.runtime.commands import RuntimeCommandResult, RuntimeCommandType
from qts.runtime.control_plane import RuntimeCommandExecutor


class OperationsService:
    """Owns operational state without leaking runtime internals into API routes."""

    def __init__(
        self,
        *,
        kill_switches: KillSwitchRegistry | None = None,
        operator_status: OperatorDashboardStatusDTO | None = None,
        command_executor: RuntimeCommandExecutor | None = None,
    ) -> None:
        """Create operational command routing bound to an optional runtime executor.

        When ``command_executor`` is provided, lifecycle and kill-switch activation
        act on the bound RuntimeSession; otherwise those commands raise
        ``RuntimeCommandNotBound`` rather than mutating shadow state.
        """
        self._lifecycle = RuntimeLifecycleService()
        self._runtime_mode = "paper"
        self._kill_switch_commands = KillSwitchCommandService(kill_switches=kill_switches)
        self._dashboard = OperatorDashboardService(status_override=operator_status)
        self._command_handler = OperationsCommandHandler(
            lifecycle=self._lifecycle,
            kill_switch_commands=self._kill_switch_commands,
            command_executor=command_executor,
        )
        self._commands = OperationsCommandRouter(handler=self._command_handler.handle)

    def start_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Start runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.START,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def start_runtime_result(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Start runtime processing and return the auditable command result."""
        return self._submit_runtime_command_result(
            RuntimeCommandType.START,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def stop_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Stop runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.STOP,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def stop_runtime_result(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Stop runtime processing and return the auditable command result."""
        return self._submit_runtime_command_result(
            RuntimeCommandType.STOP,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def pause_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Pause runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.PAUSE,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def pause_runtime_result(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Pause runtime processing and return the auditable command result."""
        return self._submit_runtime_command_result(
            RuntimeCommandType.PAUSE,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def resume_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Resume runtime processing through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.RESUME,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def resume_runtime_result(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Resume runtime processing and return the auditable command result."""
        return self._submit_runtime_command_result(
            RuntimeCommandType.RESUME,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def enter_observation(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Enter observation mode through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.ENTER_OBSERVATION,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def enter_observation_result(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Enter observation mode and return the auditable command result."""
        return self._submit_runtime_command_result(
            RuntimeCommandType.ENTER_OBSERVATION,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def exit_observation(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeStateDTO:
        """Exit observation mode through the command bus."""
        return self._submit_runtime_state_command(
            RuntimeCommandType.EXIT_OBSERVATION,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def exit_observation_result(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Exit observation mode and return the auditable command result."""
        return self._submit_runtime_command_result(
            RuntimeCommandType.EXIT_OBSERVATION,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def activate_kill_switch(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> KillSwitchStateDTO:
        """Activate a kill switch through the command bus."""
        result = self._commands.submit(
            RuntimeCommandType.ACTIVATE_KILL_SWITCH,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
            reason=command.reason,
            payload={
                "scope": command.scope,
                "scope_id": command.scope_id,
                "reason": command.reason,
            },
        )
        return self._kill_switch_state_from_result(result)

    def activate_kill_switch_result(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Activate a kill switch and return the auditable command result."""
        result = self._commands.submit(
            RuntimeCommandType.ACTIVATE_KILL_SWITCH,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
            reason=command.reason,
            payload={
                "scope": command.scope,
                "scope_id": command.scope_id,
                "reason": command.reason,
            },
        )
        return OperationsCommandRouter.result_dto(result)

    def deactivate_kill_switch(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str = "system",
        operator_role: str = "operator",
        authorization_scope: str = "runtime:operator",
        idempotency_key: str | None = None,
    ) -> KillSwitchStateDTO:
        """Deactivate a kill switch through the command bus."""
        result = self._submit_deactivate_kill_switch_command(
            command,
            operator_id=operator_id,
            operator_role=operator_role,
            authorization_scope=authorization_scope,
            idempotency_key=idempotency_key,
        )
        return self._kill_switch_state_from_result(result)

    def deactivate_kill_switch_result(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str = "system",
        operator_role: str = "operator",
        authorization_scope: str = "runtime:operator",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Deactivate a kill switch and return the auditable command result."""
        result = self._submit_deactivate_kill_switch_command(
            command,
            operator_id=operator_id,
            operator_role=operator_role,
            authorization_scope=authorization_scope,
            idempotency_key=idempotency_key,
        )
        return OperationsCommandRouter.result_dto(result)

    def _submit_deactivate_kill_switch_command(
        self,
        command: KillSwitchCommandDTO,
        *,
        operator_id: str,
        operator_role: str,
        authorization_scope: str,
        idempotency_key: str | None,
    ) -> RuntimeCommandResult:
        return self._commands.submit(
            RuntimeCommandType.DEACTIVATE_KILL_SWITCH,
            operator_id=operator_id,
            operator_role=operator_role,
            authorization_scope=authorization_scope,
            idempotency_key=idempotency_key,
            reason=command.reason,
            payload={
                "scope": command.scope,
                "scope_id": command.scope_id,
                "reason": command.reason,
            },
        )

    def reconcile_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Request a runtime reconciliation through the command bus."""
        result = self._commands.submit(
            RuntimeCommandType.RECONCILE,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
        return OperationsCommandRouter.result_dto(result)

    def snapshot_runtime(
        self,
        *,
        operator_id: str = "system",
        idempotency_key: str | None = None,
    ) -> RuntimeCommandResultDTO:
        """Request a runtime snapshot through the command bus."""
        result = self._commands.submit(
            RuntimeCommandType.SNAPSHOT,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
        return OperationsCommandRouter.result_dto(result)

    def operator_status(self) -> OperatorDashboardStatusDTO:
        """Return the application-owned operator dashboard state."""
        return self._dashboard.status(
            runtime_state=self._lifecycle.state,
            runtime_mode=self._runtime_mode,
            kill_switch_state=self._kill_switch_commands.state,
        )

    def _submit_runtime_state_command(
        self,
        command_type: RuntimeCommandType,
        *,
        operator_id: str,
        idempotency_key: str | None,
    ) -> RuntimeStateDTO:
        return self._commands.submit_state(
            command_type,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )

    def _submit_runtime_command_result(
        self,
        command_type: RuntimeCommandType,
        *,
        operator_id: str,
        idempotency_key: str | None,
    ) -> RuntimeCommandResultDTO:
        result = self._commands.submit(
            command_type,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
        )
        return OperationsCommandRouter.result_dto(result)

    @staticmethod
    def _kill_switch_state_from_result(result: RuntimeCommandResult) -> KillSwitchStateDTO:
        """Map command result evidence into the stable kill-switch DTO."""
        scope = result.evidence.get("scope")
        scope_id = result.evidence.get("scope_id")
        active = result.evidence.get("active")
        reason = result.evidence.get("reason")
        if not isinstance(scope, str):
            raise RuntimeError("kill-switch command result did not include scope evidence")
        if scope_id is not None and not isinstance(scope_id, str):
            raise RuntimeError("kill-switch command result included invalid scope_id evidence")
        if not isinstance(active, bool):
            raise RuntimeError("kill-switch command result did not include active evidence")
        if not isinstance(reason, str):
            raise RuntimeError("kill-switch command result did not include reason evidence")
        return KillSwitchStateDTO(scope=scope, scope_id=scope_id, active=active, reason=reason)


__all__ = ["OperationsService"]
