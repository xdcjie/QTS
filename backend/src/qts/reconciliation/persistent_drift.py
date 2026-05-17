"""Persistent reconciliation drift kill switch.

When the same drift key surfaces as DIVERGENT for N consecutive
reconciliation cycles, the kill switch trips. The runtime contract pairs
this with the existing kill-switch path so further orders cannot
accumulate beyond the broker's actual state.

Stateless ``ReconciliationEngine`` produces reports; this owner accumulates
the cross-cycle history and returns a decision per cycle.
"""

from __future__ import annotations

from dataclasses import dataclass

from qts.reconciliation.drift import DriftKind
from qts.reconciliation.report import ReconciliationReport


@dataclass(frozen=True, slots=True)
class PersistentDriftConfig:
    """Activation threshold for the persistent drift kill switch."""

    consecutive_threshold: int = 3

    def __post_init__(self) -> None:
        if self.consecutive_threshold <= 0:
            raise ValueError("consecutive_threshold must be positive")


@dataclass(frozen=True, slots=True)
class PersistentDriftDecision:
    """Result of one ``observe`` cycle."""

    tripped: bool
    tripped_key: str | None = None


class PersistentDriftKillSwitch:
    """Track consecutive DIVERGENT reports on the same drift key."""

    def __init__(self, config: PersistentDriftConfig | None = None) -> None:
        self._config = config or PersistentDriftConfig()
        self._streak_key: str | None = None
        self._streak_count = 0
        self._tripped: bool = False
        self._tripped_key: str | None = None

    @property
    def tripped(self) -> bool:
        """Return whether the switch has activated."""
        return self._tripped

    @property
    def tripped_key(self) -> str | None:
        """Return the drift key that caused activation, if any."""
        return self._tripped_key

    def observe(self, report: ReconciliationReport) -> PersistentDriftDecision:
        """Process one reconciliation report and return the current decision.

        A report is "divergent" when it contains at least one DIVERGENT item.
        Among such items, the lexicographically smallest key is used as the
        streak key so alternating drift on multiple keys does not satisfy the
        threshold for any single key.

        Once tripped, the switch stays tripped regardless of subsequent
        reports; recovery is an explicit out-of-band action (e.g. operator
        kill-switch reset).
        """
        if self._tripped:
            return PersistentDriftDecision(tripped=True, tripped_key=self._tripped_key)

        divergent_keys = sorted(
            item.key for item in report.items if item.kind is DriftKind.DIVERGENT
        )
        if not divergent_keys:
            self._streak_key = None
            self._streak_count = 0
            return PersistentDriftDecision(tripped=False)

        focus_key = divergent_keys[0]
        if self._streak_key == focus_key:
            self._streak_count += 1
        else:
            self._streak_key = focus_key
            self._streak_count = 1

        if self._streak_count >= self._config.consecutive_threshold:
            self._tripped = True
            self._tripped_key = focus_key
            return PersistentDriftDecision(tripped=True, tripped_key=focus_key)
        return PersistentDriftDecision(tripped=False)


__all__ = [
    "PersistentDriftConfig",
    "PersistentDriftDecision",
    "PersistentDriftKillSwitch",
]
