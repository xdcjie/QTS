"""Reconciliation engine and snapshot comparison orchestration."""

from __future__ import annotations

from decimal import Decimal

from .drift import compare_cash, compare_orders, compare_positions, drift_sort_key
from .report import ReconciliationReport
from .snapshots import ReconciliationSnapshot
from .startup_gate import StartupReconciliationDecision, startup_reconciliation_gate


class ReconciliationEngine:
    """Deterministic snapshot reconciliation service."""

    def __init__(self, *, tolerance: Decimal = Decimal("0")) -> None:
        """Create the engine with a non-negative tolerance."""
        if tolerance < Decimal("0"):
            raise ValueError("tolerance must be non-negative")
        self._tolerance = tolerance

    def reconcile(
        self,
        *,
        internal: ReconciliationSnapshot,
        broker: ReconciliationSnapshot,
        tolerance: Decimal | None = None,
    ) -> ReconciliationReport:
        """Reconcile two snapshots and return a drift report."""
        return reconcile_snapshots(
            internal=internal,
            broker=broker,
            tolerance=self._effective_tolerance(tolerance),
        )

    def startup_gate(self, report: ReconciliationReport) -> StartupReconciliationDecision:
        """Return startup decision from a drift report."""
        return startup_reconciliation_gate(report)

    def _effective_tolerance(self, override: Decimal | None) -> Decimal:
        """Resolve effective tolerance with validation."""
        if override is None:
            return self._tolerance
        if override < Decimal("0"):
            raise ValueError("tolerance must be non-negative")
        return override


def reconcile_snapshots(
    *,
    internal: ReconciliationSnapshot,
    broker: ReconciliationSnapshot,
    tolerance: Decimal = Decimal("0"),
) -> ReconciliationReport:
    """Compare broker and internal snapshots into a deterministic drift report."""
    if internal.account_id != broker.account_id:
        raise ValueError("cannot reconcile different accounts")
    if tolerance < Decimal("0"):
        raise ValueError("tolerance must be non-negative")

    items = [
        *compare_orders(internal.orders, broker.orders),
        *compare_positions(internal.positions, broker.positions, tolerance),
        *compare_cash(internal.cash, broker.cash, tolerance),
    ]
    return ReconciliationReport(
        account_id=internal.account_id,
        items=tuple(sorted(items, key=lambda item: drift_sort_key(item.key))),
    )


__all__ = ["ReconciliationEngine", "reconcile_snapshots"]
