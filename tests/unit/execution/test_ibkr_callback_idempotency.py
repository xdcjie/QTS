from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qts.execution.adapters.ibkr_order_execution import IbkrOrderExecutionAdapter


def test_ibkr_callback_normalizer_drops_duplicate_order_status_callbacks() -> None:
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import ExecutionReportStatus
    from qts.execution.adapters.ibkr_callback_normalizer import IbkrCallbackNormalizer
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderStatusPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    status = IbkrOrderStatusPayload(
        report_id="status-1",
        broker_order_id="ibkr-001",
        status="Submitted",
        perm_id="perm-001",
    )
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-001",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-ibkr"),
        submitted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
    )
    order_map.attach_ibkr_order_id(client_order_id="client-001", ibkr_order_id="ibkr-001")
    normalizer = IbkrCallbackNormalizer(
        account_id="DU1234567",
        symbol_mapping=mapping,
        order_map=order_map,
    )

    first = normalizer.on_order_status(status)
    duplicate = normalizer.on_order_status(status)

    assert first is not None
    assert first.status is ExecutionReportStatus.ACCEPTED
    assert duplicate is None
    assert normalizer.callback_events[-1].kind == "ibkr_order_callback_duplicate_dropped"
    assert normalizer.callback_events[-1].reason == "order_status_already_seen"


def test_duplicate_order_status_is_idempotent() -> None:
    from qts.domain.orders import ExecutionReportStatus
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderStatusPayload

    adapter = _adapter_with_order_map()

    first = adapter.on_order_status(
        IbkrOrderStatusPayload(
            report_id="status-1",
            broker_order_id="ibkr-001",
            status="Submitted",
            perm_id="perm-001",
        )
    )
    duplicate = adapter.on_order_status(
        IbkrOrderStatusPayload(
            report_id="status-1-dup",
            broker_order_id="ibkr-001",
            status="Submitted",
            perm_id="perm-001",
        )
    )

    assert first is not None
    assert first.status is ExecutionReportStatus.ACCEPTED
    assert duplicate is None
    assert adapter.callback_events[-1].kind == "ibkr_order_callback_duplicate_dropped"
    assert adapter.callback_events[-1].reason == "order_status_already_seen"


def test_execution_before_open_order_is_quarantined_or_later_resolved() -> None:
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrExecutionPayload,
        IbkrOpenOrderPayload,
    )

    adapter = _adapter_with_order_map(attach_broker_id=False)

    unresolved = adapter.on_execution(
        IbkrExecutionPayload(
            report_id="exec-before-open-order",
            broker_order_id="ibkr-001",
            execution_id="exec-001",
            filled_quantity=Decimal("1"),
            fill_price=Decimal("101.25"),
            account_id="DU1234567",
        )
    )
    adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="exec-001",
            commission=Decimal("1.25"),
            currency="USD",
        )
    )
    adapter.on_open_order(
        IbkrOpenOrderPayload(
            report_id="open-order-late",
            broker_order_id="ibkr-001",
            client_order_id="client-001",
            status="Submitted",
            broker_symbol="AAPL",
            side="BUY",
            quantity=Decimal("1"),
        )
    )
    resolved = adapter.resolve_quarantined_callbacks()

    assert unresolved is None
    assert adapter.quarantined_executions == ()
    assert len(resolved) == 1
    assert resolved[0].fill_id == "exec-001"
    assert resolved[0].commission == Decimal("1.25")


def test_late_commission_updates_cost_without_duplicate_fill() -> None:
    from qts.domain.orders import ExecutionReport
    from qts.execution.broker import BrokerCommissionReport
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrExecutionPayload,
    )

    adapter = _adapter_with_order_map()

    adapter.on_execution(
        IbkrExecutionPayload(
            report_id="exec-001",
            broker_order_id="ibkr-001",
            execution_id="exec-001",
            filled_quantity=Decimal("1"),
            fill_price=Decimal("101.25"),
            account_id="DU1234567",
        )
    )
    fill = adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="exec-001",
            commission=Decimal("1.25"),
            currency="USD",
        )
    )
    late_commission = adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="exec-001",
            commission=Decimal("1.30"),
            currency="USD",
        )
    )

    assert fill is not None
    assert isinstance(fill, ExecutionReport)
    assert fill.fill_id == "exec-001"
    assert isinstance(late_commission, BrokerCommissionReport)
    assert late_commission.commission == Decimal("1.30")
    assert adapter.callback_events[-1].reason == "commission_for_completed_execution"


def test_duplicate_exec_id_applied_once() -> None:
    from qts.domain.orders import ExecutionReport
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrExecutionPayload,
    )

    adapter = _adapter_with_order_map()
    execution = IbkrExecutionPayload(
        report_id="exec-001",
        broker_order_id="ibkr-001",
        execution_id="exec-duplicate",
        filled_quantity=Decimal("0.5"),
        fill_price=Decimal("101.25"),
        account_id="DU1234567",
    )

    adapter.on_execution(execution)
    first = adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="exec-duplicate",
            commission=Decimal("0.75"),
            currency="USD",
        )
    )
    duplicate = adapter.on_execution(execution)

    assert first is not None
    assert isinstance(first, ExecutionReport)
    assert first.filled_quantity == Decimal("0.5")
    assert duplicate is None
    assert adapter.callback_events[-1].reason == "execution_already_completed"


def test_open_order_unknown_internal_order_quarantined() -> None:
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOpenOrderPayload

    adapter = _adapter_with_order_map()

    adapter.on_open_order(
        IbkrOpenOrderPayload(
            report_id="unknown-open-order",
            broker_order_id="ibkr-unknown",
            client_order_id="client-unknown",
            status="Submitted",
            broker_symbol="AAPL",
            side="BUY",
            quantity=Decimal("1"),
        )
    )

    assert len(adapter.quarantined_open_orders) == 1
    assert adapter.callback_events[-1].reason == "unknown_client_order_id"


def test_callback_account_mismatch_quarantined() -> None:
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrExecutionPayload

    adapter = _adapter_with_order_map()

    report = adapter.on_execution(
        IbkrExecutionPayload(
            report_id="wrong-account-exec",
            broker_order_id="ibkr-001",
            execution_id="exec-wrong-account",
            filled_quantity=Decimal("1"),
            fill_price=Decimal("101.25"),
            account_id="DU9999999",
        )
    )

    assert report is None
    assert len(adapter.quarantined_executions) == 1
    assert adapter.callback_events[-1].kind == "ibkr_account_callback_quarantined"
    assert adapter.callback_events[-1].reason == "wrong_account"


def test_reconnect_open_order_replay_is_idempotent() -> None:
    from qts.core.ids import AccountId
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOpenOrderPayload

    adapter = _adapter_with_order_map()
    replay = IbkrOpenOrderPayload(
        report_id="open-order-replay",
        broker_order_id="ibkr-001",
        client_order_id="client-001",
        status="Submitted",
        broker_symbol="AAPL",
        side="BUY",
        quantity=Decimal("1"),
    )

    adapter.on_open_order(replay)
    adapter.on_open_order(replay)
    snapshot = adapter.broker_reconciliation_snapshot(account_id=AccountId("acct-ibkr"))

    assert len(snapshot.orders) == 1
    assert snapshot.orders[0].order_id.value == "ord-001"


def _adapter_with_order_map(*, attach_broker_id: bool = True) -> IbkrOrderExecutionAdapter:
    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

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
    if attach_broker_id:
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
