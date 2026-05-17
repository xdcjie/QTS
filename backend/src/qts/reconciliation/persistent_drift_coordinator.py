"""Persistent drift coordinator — wires the OPT-47 kill switch to runtime safety.

``ReconciliationEngine`` remains a stateless diff producer; this coordinator
owns the cross-cycle streak counting via ``PersistentDriftKillSwitch`` and
invokes the existing safety-controller path on activation. The runtime
provides any callable that accepts ``(key, reason)`` — typically a thin
adapter around :class:`qts.runtime.safety_controller.RuntimeSafetyController`.
"""

from __future__ import annotations

from typing import Protocol

from qts.reconciliation.persistent_drift import (
    PersistentDriftConfig,
    PersistentDriftKillSwitch,
)
from qts.reconciliation.report import ReconciliationReport


class _SafetyControllerLike(Protocol):
    """Minimal safety-controller surface the coordinator depends on."""

    def activate_kill_switch_via_persistent_drift(self, *, key: str, reason: str) -> None:
        """Activate the runtime kill switch with persistent-drift evidence."""


class PersistentDriftCoordinator:
    """Feed reconciliation reports into the kill-switch streak counter.

    The first time the underlying ``PersistentDriftKillSwitch`` trips, the
    coordinator invokes the safety controller exactly once. Subsequent
    reports (even continuing divergence) do not re-activate, preventing
    duplicate kill-switch events in the audit trail.
    """

    def __init__(
        self,
        *,
        safety_controller: _SafetyControllerLike,
        config: PersistentDriftConfig | None = None,
    ) -> None:
        self._safety_controller = safety_controller
        self._kill_switch = PersistentDriftKillSwitch(config or PersistentDriftConfig())
        self._already_tripped = False

    def observe(self, report: ReconciliationReport) -> None:
        """Process one reconciliation cycle's report."""
        decision = self._kill_switch.observe(report)
        if not decision.tripped or self._already_tripped:
            return
        self._already_tripped = True
        assert decision.tripped_key is not None
        self._safety_controller.activate_kill_switch_via_persistent_drift(
            key=decision.tripped_key,
            reason=(
                f"persistent reconciliation drift on key={decision.tripped_key!r} "
                f"for {self._kill_switch._config.consecutive_threshold} consecutive cycles"
            ),
        )


__all__ = ["PersistentDriftCoordinator"]
