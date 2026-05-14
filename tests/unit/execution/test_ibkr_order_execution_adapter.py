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

    request = adapter.to_order_request(intent)
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
    assert request.broker_symbol == "AAPL"
    assert request.side == "buy"
    assert report.broker_order_id == "ibkr-001"
    assert report.fill_price == Decimal("101.25")
    assert not hasattr(adapter, "subscription_for")
    assert not hasattr(adapter, "normalize_tick")


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
            asset_class="future",
        )


def test_ibkr_order_execution_adapter_treats_pending_cancel_as_non_terminal_ack() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_transport import IbkrOrderStatusPayload
    from qts.execution.order_manager import ExecutionReportStatus
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

    assert report.status is ExecutionReportStatus.ACCEPTED
    assert report.broker_order_id == "ibkr-001"


def test_ibkr_execution_report_waits_for_commission_before_fill_report() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_transport import IbkrCommissionPayload, IbkrExecutionPayload
    from qts.execution.order_manager import ExecutionReport
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
    from qts.execution.adapters.ibkr_transport import (
        IbkrCommissionPayload,
        IbkrCommissionReport,
        IbkrExecutionPayload,
    )
    from qts.execution.order_manager import ExecutionReport
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
