"""Reconciliation report model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qts.core.ids import AccountId

from .drift import DriftItem, DriftKind


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Drift report for a single account."""

    account_id: AccountId
    items: tuple[DriftItem, ...]

    @property
    def has_drift(self) -> bool:
        """True when report contains non-tolerable mismatch."""
        return any(
            item.kind not in {DriftKind.MATCHED, DriftKind.TOLERANCE_ONLY} for item in self.items
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize reconciliation report."""
        return {
            "account_id": self.account_id.value,
            "has_drift": self.has_drift,
            "items": [item.to_dict() for item in self.items],
        }


__all__ = ["ReconciliationReport"]
