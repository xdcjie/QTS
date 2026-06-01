"""RuntimeCommandBus converts unbound runtime commands into rejected results."""

from __future__ import annotations

from qts.runtime.commands import (
    RuntimeCommand,
    RuntimeCommandBus,
    RuntimeCommandResult,
    RuntimeCommandResultStatus,
    RuntimeCommandType,
)
from qts.runtime.errors import RuntimeCommandNotBound


def test_runtime_command_bus_converts_unbound_exception_to_rejected_result() -> None:
    def handler(_command: RuntimeCommand) -> RuntimeCommandResult:
        raise RuntimeCommandNotBound("RUNTIME_SESSION_NOT_BOUND: no RuntimeSession is bound")

    bus = RuntimeCommandBus(handler=handler)

    result = bus.submit(
        RuntimeCommand(
            command_id="pause-1",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="key-1",
            operator_id="operator-1",
            runtime_instance_id="runtime-1",
        )
    )

    assert result.result_status is RuntimeCommandResultStatus.REJECTED
    assert result.reason_code == "RUNTIME_SESSION_NOT_BOUND"
    assert result.evidence["runtime_instance_id"] == "runtime-1"
