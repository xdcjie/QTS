"""Anchor: persistent drift on the same key trips the reconciliation kill switch.

Domain fact: a DIVERGENT reconciliation result on the same drift key for N
consecutive cycles is a financial-correctness emergency; the runtime must
not allow further orders to accumulate exposure beyond the broker's actual
state.

Owner: ``qts.reconciliation.persistent_drift.PersistentDriftKillSwitch``.

Forbidden shortcut: counting cycles inside ``ReconciliationEngine`` (it
should remain a stateless diff producer); kill-switch activation through
direct access to the runtime state machine.
"""

from __future__ import annotations

from qts.core.ids import AccountId
from qts.reconciliation.drift import DriftItem, DriftKind
from qts.reconciliation.persistent_drift import (
    PersistentDriftConfig,
    PersistentDriftKillSwitch,
)
from qts.reconciliation.report import ReconciliationReport


def _report(*kinds: tuple[DriftKind, str]) -> ReconciliationReport:
    return ReconciliationReport(
        account_id=AccountId("acct-1"),
        items=tuple(
            DriftItem(kind=kind, key=key, internal=None, broker=None) for kind, key in kinds
        ),
    )


def test_threshold_three_does_not_trip_on_two_cycles() -> None:
    switch = PersistentDriftKillSwitch(PersistentDriftConfig(consecutive_threshold=3))

    first = switch.observe(_report((DriftKind.DIVERGENT, "order:A")))
    second = switch.observe(_report((DriftKind.DIVERGENT, "order:A")))

    assert first.tripped is False
    assert second.tripped is False


def test_threshold_three_trips_on_third_consecutive_same_key() -> None:
    switch = PersistentDriftKillSwitch(PersistentDriftConfig(consecutive_threshold=3))

    switch.observe(_report((DriftKind.DIVERGENT, "order:A")))
    switch.observe(_report((DriftKind.DIVERGENT, "order:A")))
    third = switch.observe(_report((DriftKind.DIVERGENT, "order:A")))

    assert third.tripped is True
    assert third.tripped_key == "order:A"


def test_alternating_keys_never_trip() -> None:
    switch = PersistentDriftKillSwitch(PersistentDriftConfig(consecutive_threshold=3))

    for key in ("order:A", "order:B", "order:A", "order:B", "order:A"):
        decision = switch.observe(_report((DriftKind.DIVERGENT, key)))
        assert decision.tripped is False


def test_matched_report_resets_streak() -> None:
    switch = PersistentDriftKillSwitch(PersistentDriftConfig(consecutive_threshold=3))

    switch.observe(_report((DriftKind.DIVERGENT, "order:A")))
    switch.observe(_report((DriftKind.DIVERGENT, "order:A")))
    reset = switch.observe(_report((DriftKind.MATCHED, "order:A")))
    fourth = switch.observe(_report((DriftKind.DIVERGENT, "order:A")))

    assert reset.tripped is False
    assert fourth.tripped is False


def test_already_tripped_switch_stays_tripped() -> None:
    switch = PersistentDriftKillSwitch(PersistentDriftConfig(consecutive_threshold=2))

    switch.observe(_report((DriftKind.DIVERGENT, "order:A")))
    second = switch.observe(_report((DriftKind.DIVERGENT, "order:A")))
    assert second.tripped is True

    later = switch.observe(_report((DriftKind.MATCHED, "order:A")))
    assert later.tripped is True
    assert later.tripped_key == "order:A"
