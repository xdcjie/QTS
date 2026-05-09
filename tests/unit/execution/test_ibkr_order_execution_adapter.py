from __future__ import annotations

from decimal import Decimal


def test_ibkr_order_execution_adapter_maps_order_and_report_without_market_data_methods() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrExecutionReport,
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.order_manager import ExecutionReportStatus, OrderIntent, OrderSide
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
            status=ExecutionReportStatus.FILLED,
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
