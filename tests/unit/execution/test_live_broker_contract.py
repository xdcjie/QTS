from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import ExecutionReportStatus
from qts.execution.broker import (
    BrokerCapabilities,
    BrokerOrderRequest,
    normalize_broker_execution_report,
)
from qts.execution.order_manager import OrderSide
from qts.simulation.broker import SimulatedBrokerAdapter


def test_broker_capabilities_are_typed_and_validate_limits() -> None:
    capabilities = BrokerCapabilities(
        broker_id=BrokerId("paper"),
        supports_market_orders=True,
        supports_limit_orders=False,
        supports_cancel=True,
        supports_replace=False,
        max_order_quantity=Decimal("100"),
        supported_asset_classes=frozenset({"stock", "future"}),
    )

    assert capabilities.supports_asset_class("future")
    assert not capabilities.supports_asset_class("option")
    with pytest.raises(ValueError, match="max_order_quantity"):
        BrokerCapabilities(broker_id=BrokerId("paper"), max_order_quantity=Decimal("0"))


def test_simulated_broker_submit_cancel_and_fill_contract() -> None:
    adapter = SimulatedBrokerAdapter(broker_id=BrokerId("fake"))
    request = BrokerOrderRequest(
        order_id=OrderId("order-1"),
        client_order_id="client-order-1",
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strat-a"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    accepted = adapter.submit_order(request)
    cancelled = adapter.cancel_order(request.order_id)
    filled = adapter.emit_fill(
        order_id=request.order_id,
        quantity=Decimal("4"),
        price=Decimal("190.25"),
        fill_id="fill-1",
    )

    assert accepted.status is ExecutionReportStatus.ACCEPTED
    assert cancelled.status is ExecutionReportStatus.CANCELLED
    assert filled.instrument_id == request.instrument_id
    assert filled.account_id == request.account_id
    assert filled.broker_order_id.startswith("fake-")


def test_simulated_broker_rejects_empty_fill_id() -> None:
    adapter = SimulatedBrokerAdapter(broker_id=BrokerId("fake"))
    request = BrokerOrderRequest(
        order_id=OrderId("order-1"),
        client_order_id="client-order-1",
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strat-a"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    adapter.submit_order(request)

    with pytest.raises(ValueError, match="fill_id"):
        adapter.emit_fill(
            order_id=request.order_id,
            quantity=Decimal("4"),
            price=Decimal("190.25"),
            fill_id="",
        )


def test_broker_report_normalization_does_not_leak_vendor_object() -> None:
    adapter = SimulatedBrokerAdapter(broker_id=BrokerId("fake"))
    request = BrokerOrderRequest(
        order_id=OrderId("order-1"),
        client_order_id="client-order-1",
        account_id=AccountId("acct-a"),
        strategy_id=None,
        instrument_id=InstrumentId("FUTURE.CME.ES.202606"),
        side=OrderSide.SELL,
        quantity=Decimal("2"),
    )
    vendor_report = adapter.submit_order(request)

    report = normalize_broker_execution_report(vendor_report)

    assert report.broker_order_id == vendor_report.broker_order_id
    assert not hasattr(report, "vendor_payload")
