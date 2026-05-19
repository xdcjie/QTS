"""Anchor: BrokerExecutionReport carries fill_time end-to-end.

Domain fact: OPT-73 fixed backtest holding_bars by threading
fill_time through SimulatedExecutionAdapter -> ExecutionReport ->
ApplyFill -> AccountActor. But the live path goes through
BrokerExecutionAdapter, which receives BrokerExecutionReport from
the broker layer and converts it via
``normalize_broker_execution_report``. That normalizer dropped any
broker-supplied timestamp, so live runs would re-introduce the
``opened_at=null`` bug we just killed in backtest.

Owner: ``qts.execution.broker.BrokerExecutionReport`` (new field) +
``qts.execution.broker.normalize_broker_execution_report``
(propagates field) + ``qts.execution.adapters.broker_execution_adapter
.BrokerExecutionAdapter.execute_market_order`` (falls back to
bar_time when broker omits a fill timestamp).

Forbidden shortcut: silently dropping broker-supplied fill_time;
hardcoding fill_time=None on live execution; making the field
required on broker reports that legitimately don't have one (e.g.
ACCEPTED-only acknowledgements).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import ExecutionReportStatus, OrderIntent, OrderSide, OrderType
from qts.domain.orders.order_spec import OrderSpec
from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
from qts.execution.broker import (
    BrokerAdapter,
    BrokerCapabilities,
    BrokerExecutionReport,
    BrokerOrderRequest,
    normalize_broker_execution_report,
)


def test_broker_execution_report_can_carry_fill_time() -> None:
    """BrokerExecutionReport must expose a fill_time field for live timestamps."""
    fill_time = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    report = BrokerExecutionReport(
        report_id="r1",
        broker_id=BrokerId("ibkr"),
        broker_order_id="bo1",
        order_id=OrderId("o1"),
        account_id=AccountId("a1"),
        strategy_id=StrategyId("s1"),
        instrument_id=InstrumentId("FUTURE.CME.GC.GCG4"),
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("2000"),
        fill_id="f1",
        fill_time=fill_time,
    )
    assert report.fill_time == fill_time


def test_normalize_broker_execution_report_propagates_fill_time() -> None:
    """The broker-to-runtime normalizer must carry fill_time across the boundary."""
    fill_time = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    broker_report = BrokerExecutionReport(
        report_id="r1",
        broker_id=BrokerId("ibkr"),
        broker_order_id="bo1",
        order_id=OrderId("o1"),
        account_id=AccountId("a1"),
        strategy_id=StrategyId("s1"),
        instrument_id=InstrumentId("FUTURE.CME.GC.GCG4"),
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("2000"),
        fill_id="f1",
        fill_time=fill_time,
    )
    runtime_report = normalize_broker_execution_report(broker_report)
    assert runtime_report.fill_time == fill_time


def test_normalize_broker_execution_report_passes_through_missing_fill_time() -> None:
    """Reports without a broker timestamp normalize to fill_time=None (no crash)."""
    broker_report = BrokerExecutionReport(
        report_id="r1",
        broker_id=BrokerId("ibkr"),
        broker_order_id="bo1",
        order_id=OrderId("o1"),
        account_id=AccountId("a1"),
        strategy_id=StrategyId("s1"),
        instrument_id=InstrumentId("FUTURE.CME.GC.GCG4"),
        status=ExecutionReportStatus.ACCEPTED,
    )
    runtime_report = normalize_broker_execution_report(broker_report)
    assert runtime_report.fill_time is None


def _make_broker_stub(*, broker_fill_time: datetime | None) -> BrokerAdapter:
    """A minimal BrokerAdapter that fills with a fixed (or absent) timestamp."""

    class _Stub:
        @property
        def capabilities(self) -> BrokerCapabilities:
            return BrokerCapabilities(broker_id=BrokerId("ibkr"))

        def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport:
            return BrokerExecutionReport(
                report_id=f"{request.client_order_id}-r1",
                broker_id=BrokerId("ibkr"),
                broker_order_id="bo1",
                order_id=request.order_id,
                account_id=request.account_id,
                strategy_id=request.strategy_id,
                instrument_id=request.instrument_id,
                status=ExecutionReportStatus.FILLED,
                filled_quantity=request.quantity,
                fill_price=Decimal("2000"),
                fill_id="f1",
                fill_time=broker_fill_time,
            )

        def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport:  # pragma: no cover
            raise NotImplementedError

    return _Stub()


@pytest.mark.parametrize(
    "broker_fill_time,bar_time,expected",
    [
        # Broker provides a real fill_time → use it.
        (
            datetime(2024, 1, 2, 14, 31, 12, tzinfo=UTC),
            datetime(2024, 1, 2, 14, 31, tzinfo=UTC),
            datetime(2024, 1, 2, 14, 31, 12, tzinfo=UTC),
        ),
        # Broker omits fill_time → fall back to bar_time (best the runtime knows).
        (
            None,
            datetime(2024, 1, 2, 14, 31, tzinfo=UTC),
            datetime(2024, 1, 2, 14, 31, tzinfo=UTC),
        ),
        # Both absent → propagate None.
        (None, None, None),
    ],
)
def test_broker_execution_adapter_prefers_broker_fill_time_then_bar_time(
    broker_fill_time: datetime | None,
    bar_time: datetime | None,
    expected: datetime | None,
) -> None:
    account_id = AccountId("a1")
    strategy_id = StrategyId("s1")
    adapter = BrokerExecutionAdapter(
        broker=_make_broker_stub(broker_fill_time=broker_fill_time),
        account_id=account_id,
        strategy_id=strategy_id,
    )
    report = adapter.execute_market_order(
        OrderIntent(
            order_id=OrderId("o1"),
            instrument_id=InstrumentId("FUTURE.CME.GC.GCG4"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            account_id=account_id,
            order_spec=OrderSpec(order_type=OrderType.MARKET),
        ),
        broker_order_id="bo1",
        market_price=Decimal("2000"),
        account_id=account_id,
        strategy_id=strategy_id,
        client_order_id="client-1",
        bar_time=bar_time,
    )
    assert report.fill_time == expected
