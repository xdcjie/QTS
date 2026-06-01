"""Every operator command must bind to a real RuntimeSession."""

from __future__ import annotations

from qts.application.services.kill_switch_commands import KillSwitchCommandService
from qts.application.services.operations_command_handler import OperationsCommandHandler
from qts.application.services.runtime_lifecycle import RuntimeLifecycleService
from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandBus,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)


def test_all_operator_commands_reject_without_bound_runtime_session() -> None:
    handler = OperationsCommandHandler(
        lifecycle=RuntimeLifecycleService(),
        kill_switch_commands=KillSwitchCommandService(),
    )
    bus = RuntimeCommandBus(handler=handler.handle)

    for command_type in RuntimeCommandType:
        command = RuntimeCommand(
            command_id=f"{command_type.value}-1",
            command_type=command_type,
            idempotency_key=f"{command_type.value}-key",
            operator_id="ops-a",
            authorization_scope=(
                "runtime:safety:write"
                if command_type is RuntimeCommandType.DEACTIVATE_KILL_SWITCH
                else "runtime:operator"
            ),
            reason="operator requested",
            payload={"scope": "global", "reason": "operator requested"},
        )

        result = bus.submit(command)

        assert result.result_status is RuntimeCommandResultStatus.REJECTED, command_type
        assert result.reason_code == "RUNTIME_SESSION_NOT_BOUND", command_type
        assert result.evidence["runtime_instance_id"] == "local-runtime"
