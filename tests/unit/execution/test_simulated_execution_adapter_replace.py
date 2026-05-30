"""The simulated execution adapter acknowledges replace deterministically.

QTS-FINAL-007 implements ``ExecutionAdapter.replace_order``. The simulated
adapter accepts the modified order immediately, returning an ``ACCEPTED`` report
(distinct ``-replace-1`` report id) so the order state machine confirms the
replace.
"""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, CorrelationId, OrderId, StrategyId
from qts.domain.orders import ExecutionReportStatus
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.runtime.config import BacktestCostModel


def test_simulated_replace_order_returns_accepted_report() -> None:
    adapter = SimulatedExecutionAdapter(cost_model=BacktestCostModel())

    report = adapter.replace_order(
        OrderId("ord-001"),
        broker_order_id="broker-001",
        new_quantity=Decimal("25"),
        account_id=AccountId("acct-1"),
        strategy_id=StrategyId("strat-1"),
        client_order_id="cli-1",
        correlation_id=CorrelationId("corr-1"),
    )

    assert report.status is ExecutionReportStatus.ACCEPTED
    assert report.broker_order_id == "broker-001"
    assert report.report_id == "broker-001-replace-1"
