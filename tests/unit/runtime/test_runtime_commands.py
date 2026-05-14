from __future__ import annotations

from datetime import UTC, datetime


def test_runtime_command_bus_returns_same_result_for_duplicate_command_key() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls: list[RuntimeCommand] = []

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        calls.append(command)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            completed_at=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence={"state": "paused"},
        )

    bus = RuntimeCommandBus(handler=handler)
    first = bus.submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="pause-key",
            operator_id="ops-a",
        )
    )
    second = bus.submit(
        RuntimeCommand(
            command_id="cmd-002",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="pause-key",
            operator_id="ops-a",
        )
    )

    assert second == first
    assert [command.command_id for command in calls] == ["cmd-001"]


def test_runtime_command_result_requires_failure_reason_for_rejected_command() -> None:
    import pytest
    from qts.runtime.commands import RuntimeCommandResult, RuntimeCommandResultStatus

    with pytest.raises(ValueError, match="failure_reason"):
        RuntimeCommandResult(
            command_id="cmd-001",
            idempotency_key="key-1",
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.REJECTED,
        )


def test_runtime_command_bus_scopes_idempotency_by_command_type() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls: list[RuntimeCommand] = []

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        calls.append(command)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            completed_at=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence={"command_type": command.command_type.value},
        )

    bus = RuntimeCommandBus(handler=handler)
    pause = bus.submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="shared-key",
            operator_id="ops-a",
        )
    )
    reconcile = bus.submit(
        RuntimeCommand(
            command_id="cmd-002",
            command_type=RuntimeCommandType.RECONCILE,
            idempotency_key="shared-key",
            operator_id="ops-a",
        )
    )

    assert pause.evidence["command_type"] == "pause"
    assert reconcile.evidence["command_type"] == "reconcile"
    assert [command.command_type for command in calls] == [
        RuntimeCommandType.PAUSE,
        RuntimeCommandType.RECONCILE,
    ]
