from __future__ import annotations

from decimal import Decimal

import pytest


def test_ibkr_order_execution_adapter_maps_order_and_report_without_market_data_methods() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrExecutionReport,
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.broker import BrokerExecutionReportStatus
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=7497,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    request = adapter.to_order_request(intent, client_order_id="client-ibkr-001")
    report = adapter.normalize_execution_report(
        IbkrExecutionReport(
            report_id="rpt-001",
            broker_order_id="ibkr-001",
            status=BrokerExecutionReportStatus.FILLED,
            filled_quantity=Decimal("10"),
            fill_price=Decimal("101.25"),
            fill_id="fill-001",
        )
    )

    assert request.account_id == "DU1234567"
    assert request.client_order_id == "client-ibkr-001"
    assert request.broker_symbol == "AAPL"
    assert request.side == "buy"
    assert report.broker_order_id == "ibkr-001"
    assert report.fill_price == Decimal("101.25")
    assert not hasattr(adapter, "subscription_for")
    assert not hasattr(adapter, "normalize_tick")


def test_broker_callback_quarantine_owns_unresolved_callback_collections() -> None:
    from qts.execution.adapters.broker_callback_quarantine import BrokerCallbackQuarantine

    quarantine = BrokerCallbackQuarantine()

    assert quarantine.__class__.__module__ == "qts.execution.adapters.broker_callback_quarantine"
    assert quarantine.has_unresolved is False


def test_ibkr_order_execution_adapter_checks_order_capabilities() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.broker import BrokerCapabilities, BrokerOrderType, TimeInForce
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        capabilities=BrokerCapabilities(
            broker_id=BrokerId("IBKR"),
            supports_market_orders=True,
            supports_limit_orders=True,
            supports_cancel=True,
            supports_replace=False,
            supports_fractional=False,
            supports_short=False,
            supported_asset_classes=frozenset({"equity"}),
            supported_time_in_force=frozenset({TimeInForce.DAY}),
        ),
    )

    limit_request = adapter.to_order_request(
        OrderIntent(
            order_id=OrderId("ord-limit"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("10"),
        ),
        client_order_id="client-limit",
        order_type=BrokerOrderType.LIMIT,
        limit_price=Decimal("99.50"),
        time_in_force=TimeInForce.DAY,
        asset_class="equity",
    )

    assert limit_request.order_type is BrokerOrderType.LIMIT
    assert limit_request.limit_price == Decimal("99.50")
    assert limit_request.time_in_force is TimeInForce.DAY
    adapter.validate_cancel_supported()
    with pytest.raises(ValueError, match="replace"):
        adapter.validate_replace_supported()
    with pytest.raises(ValueError, match="fractional"):
        adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ord-fractional"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("1.5"),
            ),
            client_order_id="client-fractional",
            asset_class="equity",
        )
    with pytest.raises(ValueError, match="short"):
        adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ord-short"),
                instrument_id=instrument_id,
                side=OrderSide.SELL,
                quantity=Decimal("1"),
            ),
            client_order_id="client-short",
            asset_class="equity",
            opens_short=True,
        )
    with pytest.raises(ValueError, match="asset class"):
        adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ord-future"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("1"),
            ),
            client_order_id="client-future",
            asset_class="future",
        )

    lot_constrained_adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        capabilities=BrokerCapabilities(
            broker_id=BrokerId("IBKR"),
            supports_market_orders=True,
            supports_fractional=True,
            min_order_quantity=Decimal("1"),
            lot_size=Decimal("5"),
        ),
    )
    with pytest.raises(ValueError, match="minimum order quantity"):
        lot_constrained_adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ord-small"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("0.5"),
            ),
            client_order_id="client-small",
        )
    with pytest.raises(ValueError, match="lot size"):
        lot_constrained_adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ord-lot"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("3"),
            ),
            client_order_id="client-lot",
        )


def test_ibkr_order_execution_adapter_treats_pending_cancel_as_non_terminal_ack() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import ExecutionReportStatus
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderStatusPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )

    report = adapter.on_order_status(
        IbkrOrderStatusPayload(
            report_id="status-pending-cancel",
            broker_order_id="ibkr-001",
            status="PendingCancel",
        )
    )

    assert report is not None
    assert report.status is ExecutionReportStatus.ACCEPTED
    assert report.broker_order_id == "ibkr-001"


def test_ibkr_order_execution_adapter_builds_broker_reconciliation_snapshot() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.order_manager import OrderSide
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrAccountSummaryPayload,
        IbkrOpenOrderPayload,
        IbkrPositionPayload,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    account_id = AccountId("acct-ibkr")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-ord-001",
        account_id=account_id,
        strategy_id=StrategyId("strategy-ibkr"),
        submitted_at=datetime(2026, 5, 14, 12, 0, tzinfo=UTC),
    )
    adapter = IbkrOrderExecutionAdapter(
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

    adapter.on_open_order(
        IbkrOpenOrderPayload(
            report_id="open-100",
            broker_order_id="100",
            client_order_id="client-ord-001",
            perm_id="99001",
            status="Submitted",
            broker_symbol="AAPL",
            side="BUY",
            quantity=Decimal("3"),
        )
    )
    adapter.on_position(
        IbkrPositionPayload(
            account_id="DU1234567",
            broker_symbol="AAPL",
            quantity=Decimal("3"),
        )
    )
    adapter.on_account_summary(
        IbkrAccountSummaryPayload(
            account_id="DU1234567",
            tag="TotalCashValue",
            value=Decimal("10000"),
            currency="USD",
        )
    )

    snapshot = adapter.broker_reconciliation_snapshot(account_id=account_id)

    assert snapshot.account_id == account_id
    assert [
        (order.order_id, order.instrument_id, order.side, order.quantity, order.status)
        for order in snapshot.orders
    ] == [(OrderId("ord-001"), instrument_id, OrderSide.BUY, Decimal("3"), "Submitted")]
    assert [(position.instrument_id, position.quantity) for position in snapshot.positions] == [
        (instrument_id, Decimal("3"))
    ]
    assert [(cash.currency, cash.balance) for cash in snapshot.cash] == [("USD", Decimal("10000"))]


def test_ibkr_execution_report_waits_for_commission_before_fill_report() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import ExecutionReport
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrExecutionPayload,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )

    pending = adapter.on_execution(
        IbkrExecutionPayload(
            report_id="exec-001",
            broker_order_id="runtime-broker-001",
            execution_id="fill-001",
            filled_quantity=Decimal("10"),
            fill_price=Decimal("101.25"),
        )
    )
    completed = adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="fill-001",
            commission=Decimal("1.23"),
            currency="USD",
        )
    )

    assert pending is None
    assert isinstance(completed, ExecutionReport)
    assert completed.fill_id == "fill-001"
    assert completed.commission == Decimal("1.23")


def test_ibkr_duplicate_execution_callback_does_not_emit_second_fill_report() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import ExecutionReport
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrCommissionReport,
        IbkrExecutionPayload,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )
    execution = IbkrExecutionPayload(
        report_id="exec-001",
        broker_order_id="runtime-broker-001",
        execution_id="fill-001",
        filled_quantity=Decimal("10"),
        fill_price=Decimal("101.25"),
    )
    commission = IbkrCommissionPayload(
        execution_id="fill-001",
        commission=Decimal("1.23"),
        currency="USD",
    )

    adapter.on_execution(execution)
    first = adapter.on_commission(commission)
    duplicate_execution = adapter.on_execution(execution)
    duplicate_commission = adapter.on_commission(commission)

    assert isinstance(first, ExecutionReport)
    assert duplicate_execution is None
    assert isinstance(duplicate_commission, IbkrCommissionReport)
    assert [event.kind for event in adapter.callback_events] == [
        "ibkr_execution_details_received",
        "ibkr_commission_report_received",
        "ibkr_execution_details_received",
        "ibkr_order_callback_duplicate_dropped",
        "ibkr_commission_report_received",
        "ibkr_order_callback_duplicate_dropped",
    ]


def test_ibkr_execution_idempotency_uses_account_and_broker_order_identity() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import ExecutionReport
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrExecutionPayload,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )

    adapter.on_execution(
        IbkrExecutionPayload(
            report_id="exec-001-a",
            broker_order_id="100",
            execution_id="shared-exec-id",
            filled_quantity=Decimal("1"),
            fill_price=Decimal("101.25"),
            account_id="DU1234567",
        )
    )
    first = adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="shared-exec-id",
            commission=Decimal("1.00"),
            currency="USD",
        )
    )
    adapter.on_execution(
        IbkrExecutionPayload(
            report_id="exec-001-b",
            broker_order_id="101",
            execution_id="shared-exec-id",
            filled_quantity=Decimal("2"),
            fill_price=Decimal("102.25"),
            account_id="DU1234567",
        )
    )
    second = adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="shared-exec-id",
            commission=Decimal("2.00"),
            currency="USD",
        )
    )

    assert isinstance(first, ExecutionReport)
    assert isinstance(second, ExecutionReport)
    assert first.broker_order_id == "100"
    assert second.broker_order_id == "101"
    assert second.filled_quantity == Decimal("2")


def test_ibkr_order_status_updates_broker_order_map_with_perm_id() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderStatusPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    adapter = IbkrOrderExecutionAdapter(
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
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        account_id=AccountId("acct-ibkr"),
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )
    request = adapter.to_order_request(
        intent,
        client_order_id="client-ord-001",
        strategy_id=StrategyId("strategy-ibkr"),
    )

    adapter.record_submitted_order(
        request,
        ibkr_order_id="100",
        submitted_at=datetime(2026, 5, 14, 12, 0, tzinfo=UTC),
    )
    adapter.on_order_status(
        IbkrOrderStatusPayload(
            report_id="status-100-submitted",
            broker_order_id="100",
            status="Submitted",
            perm_id="99001",
        )
    )

    by_perm_id = order_map.by_perm_id("99001")
    assert by_perm_id.internal_order_id == OrderId("ord-001")
    assert by_perm_id.client_order_id == "client-ord-001"
    assert by_perm_id.ibkr_order_id == "100"
    assert by_perm_id.status == "Submitted"
    assert by_perm_id.account_id == AccountId("acct-ibkr")
    assert by_perm_id.strategy_id == StrategyId("strategy-ibkr")


def test_ibkr_duplicate_order_status_callback_is_dropped() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderStatusPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    adapter = IbkrOrderExecutionAdapter(
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
    request = adapter.to_order_request(
        OrderIntent(
            order_id=OrderId("ord-001"),
            account_id=AccountId("acct-ibkr"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        ),
        client_order_id="client-ord-001",
        strategy_id=StrategyId("strategy-ibkr"),
    )
    adapter.record_submitted_order(
        request,
        ibkr_order_id="100",
        submitted_at=datetime(2026, 5, 14, 12, 0, tzinfo=UTC),
    )
    status = IbkrOrderStatusPayload(
        report_id="status-100-submitted",
        broker_order_id="100",
        status="Submitted",
        perm_id="99001",
    )

    first = adapter.on_order_status(status)
    duplicate = adapter.on_order_status(status)

    assert first is not None
    assert duplicate is None
    assert adapter.callback_events[-1].kind == "ibkr_order_callback_duplicate_dropped"
    assert adapter.callback_events[-1].reason == "order_status_already_seen"


def test_ibkr_cancel_resolves_ibkr_order_id_through_order_map() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    adapter = IbkrOrderExecutionAdapter(
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
    order_id = OrderId("ord-001")
    request = adapter.to_order_request(
        OrderIntent(
            order_id=order_id,
            account_id=AccountId("acct-ibkr"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        ),
        client_order_id="client-ord-001",
        strategy_id=StrategyId("strategy-ibkr"),
    )
    adapter.record_submitted_order(
        request,
        ibkr_order_id="100",
        submitted_at=datetime(2026, 5, 14, 12, 0, tzinfo=UTC),
    )

    broker_order_id = adapter.resolve_cancel_broker_order_id(
        internal_order_id=order_id,
        client_order_id="client-ord-001",
    )

    assert broker_order_id == "100"
    with pytest.raises(ValueError, match="client_order_id does not match"):
        adapter.resolve_cancel_broker_order_id(
            internal_order_id=order_id,
            client_order_id="client-other",
        )


def test_ibkr_open_order_maps_by_client_order_id_and_perm_id() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOpenOrderPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-ord-001",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-ibkr"),
        submitted_at=datetime(2026, 5, 14, 12, 0, tzinfo=UTC),
    )
    adapter = IbkrOrderExecutionAdapter(
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

    adapter.on_open_order(
        IbkrOpenOrderPayload(
            report_id="open-order-100",
            broker_order_id="100",
            client_order_id="client-ord-001",
            perm_id="99001",
            status="Submitted",
        )
    )

    by_ibkr_order_id = order_map.by_ibkr_order_id("100")
    assert by_ibkr_order_id.internal_order_id == OrderId("ord-001")
    assert by_ibkr_order_id.perm_id == "99001"
    assert by_ibkr_order_id.status == "Submitted"
    assert order_map.by_perm_id("99001").client_order_id == "client-ord-001"


def test_ibkr_unknown_execution_callback_is_quarantined() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrExecutionPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        order_map=BrokerOrderMap(),
    )
    execution = IbkrExecutionPayload(
        report_id="exec-unknown",
        broker_order_id="999",
        execution_id="fill-unknown",
        filled_quantity=Decimal("1"),
        fill_price=Decimal("101.25"),
    )

    result = adapter.on_execution(execution)

    assert result is None
    assert adapter.quarantined_executions == (execution,)
    assert [event.kind for event in adapter.callback_events] == [
        "ibkr_execution_details_received",
        "ibkr_order_callback_unresolved_quarantined",
    ]


def test_ibkr_wrong_account_execution_callback_is_quarantined() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrExecutionPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
    )
    execution = IbkrExecutionPayload(
        report_id="exec-wrong-account",
        broker_order_id="100",
        execution_id="fill-wrong-account",
        filled_quantity=Decimal("1"),
        fill_price=Decimal("101.25"),
        account_id="DU9999999",
    )

    result = adapter.on_execution(execution)

    assert result is None
    assert adapter.quarantined_executions == (execution,)
    assert adapter.has_unresolved_callbacks
    assert adapter.callback_events[-1].reason == "wrong_account"


def test_ibkr_quarantined_execution_resolves_after_open_order_mapping() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.order_manager import ExecutionReport
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrCommissionPayload,
        IbkrExecutionPayload,
        IbkrOpenOrderPayload,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-ord-001",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-ibkr"),
        submitted_at=datetime(2026, 5, 14, 12, 0, tzinfo=UTC),
    )
    adapter = IbkrOrderExecutionAdapter(
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
    execution = IbkrExecutionPayload(
        report_id="exec-before-open-order",
        broker_order_id="100",
        execution_id="fill-before-open-order",
        filled_quantity=Decimal("1"),
        fill_price=Decimal("101.25"),
        account_id="DU1234567",
    )

    assert adapter.on_execution(execution) is None
    assert adapter.on_commission(
        IbkrCommissionPayload(
            execution_id="fill-before-open-order",
            commission=Decimal("1.23"),
            currency="USD",
        )
    )
    adapter.on_open_order(
        IbkrOpenOrderPayload(
            report_id="open-order-100",
            broker_order_id="100",
            client_order_id="client-ord-001",
            status="Submitted",
        )
    )

    resolved = adapter.resolve_quarantined_callbacks()

    assert len(resolved) == 1
    assert isinstance(resolved[0], ExecutionReport)
    assert resolved[0].fill_id == "fill-before-open-order"
    assert adapter.quarantined_executions == ()
    assert adapter.has_unresolved_callbacks is False
    assert adapter.callback_events[-1].kind == "ibkr_order_callback_quarantine_resolved"


def test_ibkr_unknown_open_order_callback_is_quarantined() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOpenOrderPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        order_map=BrokerOrderMap(),
    )
    open_order = IbkrOpenOrderPayload(
        report_id="open-order-unknown",
        broker_order_id="999",
        client_order_id="client-unknown",
        perm_id="99001",
        status="Submitted",
    )

    adapter.on_open_order(open_order)

    assert adapter.quarantined_open_orders == (open_order,)
    assert [event.kind for event in adapter.callback_events] == [
        "ibkr_open_order_received",
        "ibkr_order_callback_unresolved_quarantined",
    ]


def test_ibkr_unknown_order_status_callback_is_quarantined() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrOrderStatusPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        order_map=BrokerOrderMap(),
    )
    status = IbkrOrderStatusPayload(
        report_id="status-unknown",
        broker_order_id="999",
        status="Submitted",
        perm_id="99001",
    )

    result = adapter.on_order_status(status)

    assert result is None
    assert adapter.quarantined_order_statuses == (status,)
    assert [event.kind for event in adapter.callback_events] == [
        "ibkr_order_status_received",
        "ibkr_order_callback_unresolved_quarantined",
    ]


def test_ibkr_unresolved_callbacks_block_new_order_requests() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.execution.transports.ibkr_tws_order_execution_transport import IbkrExecutionPayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU1234567",
        ),
        symbol_mapping=mapping,
        order_map=BrokerOrderMap(),
    )
    adapter.on_execution(
        IbkrExecutionPayload(
            report_id="exec-unknown",
            broker_order_id="999",
            execution_id="fill-unknown",
            filled_quantity=Decimal("1"),
            fill_price=Decimal("101.25"),
        )
    )

    with pytest.raises(RuntimeError, match="unresolved IBKR callbacks"):
        adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ord-blocked"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("1"),
            ),
            client_order_id="client-blocked",
        )
