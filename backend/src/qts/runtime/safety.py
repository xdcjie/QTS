"""Runtime safety evidence models."""

from __future__ import annotations

from dataclasses import dataclass

from qts.runtime.actors.account_actor import AccountSnapshot


@dataclass(frozen=True, slots=True)
class RuntimeKillSwitchEvidence:
    """Evidence emitted when a runtime kill switch is activated."""

    operator_id: str
    reason: str
    runtime_state: str
    active_order_ids: tuple[str, ...]
    cancelled_order_ids: tuple[str, ...]
    account_snapshot: AccountSnapshot


__all__ = [
    "RuntimeKillSwitchEvidence",
]
