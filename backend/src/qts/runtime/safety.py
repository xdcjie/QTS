"""Runtime safety evidence models."""

from __future__ import annotations

from dataclasses import dataclass

from qts.runtime.actors.account_actor import AccountSnapshot


@dataclass(frozen=True, slots=True)
class RuntimeKillSwitchDeactivateCommand:
    """Operator command to resume order submission after safety approval."""

    operator_id: str
    reason: str
    authorized: bool

    def __post_init__(self) -> None:
        """Validate kill-switch deactivate evidence fields."""
        if not self.operator_id.strip():
            raise ValueError("operator_id must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class RuntimeKillSwitchEvidence:
    """Evidence emitted when a runtime kill switch is activated."""

    run_id: str
    operator_id: str
    reason: str
    runtime_state: str
    active_order_ids: tuple[str, ...]
    cancelled_order_ids: tuple[str, ...]
    account_snapshot: AccountSnapshot
    snapshot_refs: tuple[str, ...] = ()


__all__ = [
    "RuntimeKillSwitchDeactivateCommand",
    "RuntimeKillSwitchEvidence",
]
