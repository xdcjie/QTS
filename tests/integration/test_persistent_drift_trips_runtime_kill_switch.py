"""Anchor: persistent reconciliation drift activates the runtime kill switch.

Domain fact: after N consecutive DIVERGENT reports on the same drift
key, the runtime must transition to OBSERVATION_ONLY and emit a
``runtime.kill_switch`` event. The ``PersistentDriftKillSwitch`` class
shipped in OPT-47; until OPT-63 it had no production caller.

Owner: ``qts.reconciliation.persistent_drift_coordinator`` (new) — a
thin coordinator that holds a ``PersistentDriftKillSwitch`` and invokes
the existing ``RuntimeSafetyController.activate_kill_switch`` path on
``decision.tripped``.

Forbidden shortcut: stateful counting inside ``ReconciliationEngine``;
bypassing the existing kill-switch contract.
"""

from __future__ import annotations

from qts.core.ids import AccountId
from qts.reconciliation.drift import DriftItem, DriftKind
from qts.reconciliation.persistent_drift import PersistentDriftConfig
from qts.reconciliation.persistent_drift_coordinator import PersistentDriftCoordinator
from qts.reconciliation.report import ReconciliationReport


class _RecordingSafety:
    """Stand-in for RuntimeSafetyController capturing kill-switch invocations."""

    def __init__(self) -> None:
        self.activations: list[tuple[str, str]] = []

    def activate_kill_switch_via_persistent_drift(self, *, key: str, reason: str) -> None:
        self.activations.append((key, reason))


def _report(*items: tuple[DriftKind, str]) -> ReconciliationReport:
    return ReconciliationReport(
        account_id=AccountId("acct-1"),
        items=tuple(
            DriftItem(kind=kind, key=key, internal=None, broker=None) for kind, key in items
        ),
    )


def test_three_consecutive_divergent_reports_trip_safety_controller() -> None:
    safety = _RecordingSafety()
    coordinator = PersistentDriftCoordinator(
        safety_controller=safety,
        config=PersistentDriftConfig(consecutive_threshold=3),
    )

    coordinator.observe(_report((DriftKind.DIVERGENT, "order:A")))
    coordinator.observe(_report((DriftKind.DIVERGENT, "order:A")))
    assert safety.activations == []

    coordinator.observe(_report((DriftKind.DIVERGENT, "order:A")))
    assert len(safety.activations) == 1
    key, reason = safety.activations[0]
    assert key == "order:A"
    assert "persistent" in reason.lower()


def test_safety_controller_invoked_once_even_when_drift_continues() -> None:
    """Once tripped, further DIVERGENT reports do not re-activate."""
    safety = _RecordingSafety()
    coordinator = PersistentDriftCoordinator(
        safety_controller=safety,
        config=PersistentDriftConfig(consecutive_threshold=2),
    )
    coordinator.observe(_report((DriftKind.DIVERGENT, "order:A")))
    coordinator.observe(_report((DriftKind.DIVERGENT, "order:A")))
    assert len(safety.activations) == 1
    coordinator.observe(_report((DriftKind.DIVERGENT, "order:A")))
    assert len(safety.activations) == 1


def test_matched_reports_do_not_trip_safety_controller() -> None:
    safety = _RecordingSafety()
    coordinator = PersistentDriftCoordinator(
        safety_controller=safety,
        config=PersistentDriftConfig(consecutive_threshold=3),
    )
    for _ in range(5):
        coordinator.observe(_report((DriftKind.MATCHED, "order:A")))
    assert safety.activations == []
