"""Broker-runtime reconciliation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import AccountId
from qts.execution.order_manager import OrderManagerSnapshot
from qts.reconciliation.engine import ReconciliationEngine
from qts.reconciliation.report import ReconciliationReport
from qts.reconciliation.snapshots import (
    OrderSnapshot,
    ReconciliationCashSnapshot,
    ReconciliationPositionSnapshot,
    ReconciliationSnapshot,
)
from qts.reconciliation.startup_gate import StartupReconciliationDecision
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.sinks.base import RuntimeEvent


@dataclass(frozen=True, slots=True)
class BrokerRuntimeReconciliationResult:
    """Result of a broker runtime reconciliation check."""

    report: ReconciliationReport
    runtime_event: RuntimeEvent | None = None


class BrokerRuntimeReconciliation:
    """Build snapshots and gate broker runtime trading on reconciliation drift."""

    def __init__(
        self,
        *,
        account_id: AccountId,
        engine: ReconciliationEngine | None = None,
        tolerance: Decimal = Decimal("0"),
    ) -> None:
        """Create a broker reconciliation boundary."""
        self._account_id = account_id
        self._engine = engine or ReconciliationEngine(tolerance=tolerance)

    def internal_snapshot(
        self,
        *,
        order_manager: OrderManagerSnapshot,
        account: AccountSnapshot,
    ) -> ReconciliationSnapshot:
        """Build a reconciliation snapshot from actor-owned internal snapshots."""
        return ReconciliationSnapshot(
            account_id=self._account_id,
            orders=tuple(
                OrderSnapshot(
                    order_id=order.order_id,
                    instrument_id=order.intent.instrument_id,
                    side=order.intent.side,
                    quantity=order.intent.quantity,
                    status=order.state.value,
                )
                for order in order_manager.orders
            ),
            positions=tuple(
                ReconciliationPositionSnapshot(
                    instrument_id=instrument_id,
                    quantity=position.quantity,
                )
                for instrument_id, position in account.positions.items()
            ),
            cash=tuple(
                ReconciliationCashSnapshot(currency=currency, balance=balance)
                for currency, balance in account.cash.items()
            ),
        )

    def startup_decision(
        self,
        *,
        internal: ReconciliationSnapshot,
        broker: ReconciliationSnapshot,
    ) -> StartupReconciliationDecision:
        """Return startup trading gate decision from broker/internal snapshots."""
        return self._engine.startup_gate(self._engine.reconcile(internal=internal, broker=broker))

    def periodic_check(
        self,
        *,
        internal: ReconciliationSnapshot,
        broker: ReconciliationSnapshot,
    ) -> BrokerRuntimeReconciliationResult:
        """Run a periodic reconciliation and return an optional degradation event."""
        report = self._engine.reconcile(internal=internal, broker=broker)
        if not report.has_drift:
            return BrokerRuntimeReconciliationResult(report=report)
        return BrokerRuntimeReconciliationResult(
            report=report,
            runtime_event=RuntimeEvent(
                kind="runtime.degraded",
                payload={
                    "reason": "reconciliation_drift",
                    "account_id": self._account_id.value,
                    "drift_count": len(report.items),
                },
            ),
        )


__all__ = [
    "BrokerRuntimeReconciliation",
    "BrokerRuntimeReconciliationResult",
]
