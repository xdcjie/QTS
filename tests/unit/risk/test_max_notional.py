from __future__ import annotations

from decimal import Decimal


def test_max_notional_rule_uses_multiplier_for_stock_future_and_option() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.risk import OrderRiskRequest
    from qts.risk.rules.max_notional import MaxNotionalRule

    rule = MaxNotionalRule(max_notional=Decimal("10000"))
    stock = OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("50"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
    )
    future = OrderRiskRequest(
        instrument_id=InstrumentId("FUTURE.CME.ES.202606"),
        quantity=Decimal("1"),
        price=Decimal("200"),
        multiplier=Decimal("50"),
    )
    option = OrderRiskRequest(
        instrument_id=InstrumentId("OPTION.US.AAPL.20260619.C.200"),
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("100"),
    )

    assert rule.check(stock).approved
    assert rule.check(future).approved
    assert rule.check(option).approved


def test_max_notional_rule_rejects_excessive_notional_with_reason() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.risk import OrderRiskRequest
    from qts.risk.rules.max_notional import MaxNotionalRule

    request = OrderRiskRequest(
        instrument_id=InstrumentId("FUTURE.CME.ES.202606"),
        quantity=Decimal("2"),
        price=Decimal("200"),
        multiplier=Decimal("50"),
    )

    decision = MaxNotionalRule(max_notional=Decimal("10000")).check(request)

    assert not decision.approved
    assert decision.reason_code == "MAX_NOTIONAL_EXCEEDED"
