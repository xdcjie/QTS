"""H4: a delayed/dropped IBKR commissionReport must not silently lose a fill.

Domain fact / invariant: IBKR delivers ``execDetails`` and ``commissionReport``
as separate callbacks. The normalizer stages the execution and waits for the
commission before emitting a fill. If the commission is delayed or dropped (e.g.
across a disconnect), the staged execution would be stranded forever and the
position/cash update silently lost. ``flush_pending_executions`` books such
fills with commission deferred (``0``); the real commission, if it arrives
later, is applied as a standalone ``BrokerCommissionReport`` -- never a
double-booked fill.

Owner: ``qts.execution.adapters.ibkr_fill_normalizer.IbkrFillNormalizer``
(exposed through ``IbkrCallbackNormalizer`` / ``IbkrOrderExecutionAdapter`` for
the transport lifecycle to call).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import ExecutionReport, ExecutionReportStatus
from qts.execution.adapters.ibkr_order_execution import (
    IbkrOrderExecutionAdapter,
    IbkrOrderExecutionConnection,
)
from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
from qts.execution.broker import BrokerCommissionReport
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrCommissionPayload,
    IbkrExecutionPayload,
)
from qts.registry.broker_symbol_mapping import BrokerSymbolMapping


def _adapter_with_order_map() -> IbkrOrderExecutionAdapter:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-001",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-ibkr"),
        submitted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
    )
    order_map.attach_ibkr_order_id(client_order_id="client-001", ibkr_order_id="ibkr-001")
    return IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        order_map=order_map,
    )


def _execution() -> IbkrExecutionPayload:
    return IbkrExecutionPayload(
        report_id="exec-001",
        broker_order_id="ibkr-001",
        execution_id="exec-001",
        filled_quantity=Decimal("1"),
        fill_price=Decimal("101.25"),
        account_id="DU1234567",
    )


def test_flush_books_uncommissioned_fill_so_it_is_not_lost() -> None:
    adapter = _adapter_with_order_map()

    # execDetails arrives but commissionReport never does: the fill is staged,
    # not yet emitted.
    assert adapter.on_execution(_execution()) is None

    flushed = adapter.flush_pending_executions(reason="reconnect")

    assert len(flushed) == 1
    fill = flushed[0]
    assert isinstance(fill, ExecutionReport)
    assert fill.fill_id == "exec-001"
    assert fill.filled_quantity == Decimal("1")
    assert fill.fill_price == Decimal("101.25")
    assert fill.status is ExecutionReportStatus.FILLED
    # Commission is deferred, not lost: booked as 0 now, applied later.
    assert fill.commission == Decimal("0")
    assert adapter.callback_events[-1].kind == "ibkr_fill_committed_without_commission"
    assert adapter.callback_events[-1].reason == "reconnect"


def test_late_commission_after_flush_applies_separately_without_double_booking() -> None:
    adapter = _adapter_with_order_map()
    adapter.on_execution(_execution())
    adapter.flush_pending_executions(reason="reconnect")

    # The real commission arrives after the fill was already booked: it is
    # delivered as a standalone commission adjustment, not a duplicate fill.
    late = adapter.on_commission(
        IbkrCommissionPayload(execution_id="exec-001", commission=Decimal("1.25"), currency="USD")
    )
    assert isinstance(late, BrokerCommissionReport)
    assert late.commission == Decimal("1.25")

    # Replaying execDetails (broker reconnect) is dropped as already completed.
    assert adapter.on_execution(_execution()) is None
    assert adapter.callback_events[-1].reason == "execution_already_completed"

    # Flushing again books nothing -- the fill is not emitted twice.
    assert adapter.flush_pending_executions(reason="reconnect") == ()


def test_flush_is_noop_after_normal_completion() -> None:
    adapter = _adapter_with_order_map()
    adapter.on_execution(_execution())
    fill = adapter.on_commission(
        IbkrCommissionPayload(execution_id="exec-001", commission=Decimal("1.25"), currency="USD")
    )
    assert isinstance(fill, ExecutionReport)
    assert fill.commission == Decimal("1.25")

    # Nothing is pending after a normal fill+commission; flush books nothing.
    assert adapter.flush_pending_executions(reason="shutdown") == ()
