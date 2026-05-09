from __future__ import annotations

from decimal import Decimal


def test_max_order_quantity_rule_approves_orders_within_limit() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.risk import OrderRiskRequest
    from qts.risk.rules.max_order_qty import MaxOrderQuantityRule

    request = OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("100"),
        price=Decimal("10"),
        multiplier=Decimal("1"),
    )

    assert MaxOrderQuantityRule(max_quantity=Decimal("100")).check(request).approved


def test_max_order_quantity_rule_rejects_orders_above_limit() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.risk import OrderRiskRequest
    from qts.risk.rules.max_order_qty import MaxOrderQuantityRule

    request = OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("101"),
        price=Decimal("10"),
        multiplier=Decimal("1"),
    )

    decision = MaxOrderQuantityRule(max_quantity=Decimal("100")).check(request)

    assert not decision.approved
    assert decision.reason_code == "MAX_ORDER_QTY_EXCEEDED"
