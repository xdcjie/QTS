"""Application command boundary for starting runtime modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from qts.runtime.broker_startup import BrokerRuntimeStartupDecision
from qts.runtime.mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class StartRuntimeCommand:
    """Auditable request to start a runtime from a named configuration."""

    runtime_mode: RuntimeMode | str
    config_ref: str
    operator_id: str
    idempotency_key: str
    reason: str
    startup_decision: BrokerRuntimeStartupDecision | None = None

    def __post_init__(self) -> None:
        mode = RuntimeMode.from_value(self.runtime_mode)
        object.__setattr__(self, "runtime_mode", mode)
        self._require_text(self.config_ref, "config_ref")
        self._require_text(self.operator_id, "operator_id")
        self._require_text(self.idempotency_key, "idempotency_key")
        self._require_text(self.reason, "reason")
        if self.startup_decision is not None and self.startup_decision.mode is not mode:
            raise ValueError("startup_decision mode must match runtime_mode")

    @staticmethod
    def _require_text(value: str, name: str) -> None:
        if not value.strip():
            raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class RuntimeStartResult:
    """Stable evidence returned after accepting a start-runtime command."""

    runtime_mode: RuntimeMode
    config_ref: str
    operator_id: str
    idempotency_key: str
    status: str
    order_submission_enabled: bool
    live_order_submission_enabled: bool
    reason: str
    evidence: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", dict(self.evidence))


def start_runtime(command: StartRuntimeCommand) -> RuntimeStartResult:
    """Accept a runtime start command without constructing mode-specific runtimes."""

    runtime_mode = RuntimeMode.from_value(command.runtime_mode)
    order_submission_enabled = _order_submission_enabled(command)
    live_order_submission_enabled = _live_order_submission_enabled(command)
    return RuntimeStartResult(
        runtime_mode=runtime_mode,
        config_ref=command.config_ref,
        operator_id=command.operator_id,
        idempotency_key=command.idempotency_key,
        status="started",
        order_submission_enabled=order_submission_enabled,
        live_order_submission_enabled=live_order_submission_enabled,
        reason=command.reason,
        evidence={
            "runtime_mode": runtime_mode.value,
            "config_ref": command.config_ref,
            "operator_id": command.operator_id,
            "idempotency_key": command.idempotency_key,
            "reason": command.reason,
            "startup_gate_checked": command.startup_decision is not None,
        },
    )


def _order_submission_enabled(command: StartRuntimeCommand) -> bool:
    mode = command.runtime_mode
    if mode in {RuntimeMode.BACKTEST, RuntimeMode.PAPER_BROKER, RuntimeMode.PAPER_SIMULATED}:
        return True
    if mode is RuntimeMode.LIVE_OBSERVATION:
        return False
    if mode is RuntimeMode.LIVE:
        return (
            command.startup_decision is not None
            and command.startup_decision.order_permission.allows_order_submission
        )
    return False


def _live_order_submission_enabled(command: StartRuntimeCommand) -> bool:
    if command.runtime_mode is not RuntimeMode.LIVE:
        return False
    return (
        command.startup_decision is not None
        and command.startup_decision.real_order_submission_enabled
    )


__all__ = ["RuntimeStartResult", "StartRuntimeCommand", "start_runtime"]
