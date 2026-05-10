from __future__ import annotations

from qts.core.ids import AccountId
from qts.reconciliation import (
    DriftItem,
    DriftKind,
    ReconciliationReport,
    startup_reconciliation_gate,
)


def test_startup_reconciliation_gate_blocks_trading_on_critical_drift() -> None:
    report = ReconciliationReport(
        account_id=AccountId("acct-a"),
        items=(
            DriftItem(
                kind=DriftKind.DIVERGENT,
                key="cash:USD",
                internal="100",
                broker="90",
            ),
        ),
    )

    decision = startup_reconciliation_gate(report)

    assert decision.trading_enabled is False
    assert decision.reason_code == "RECONCILIATION_DRIFT"
    assert decision.report is report
