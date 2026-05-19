"""Anchor: OrderSpecValidityRule consults the brokerage capability surface.

Domain fact: an intent whose ``order_spec.order_type`` is not in the active
brokerage's ``supported_order_types`` is rejected at risk time with
``reason_code == "UNSUPPORTED_ORDER_TYPE"`` before any adapter is touched.
Backtest and live cannot use different acceptance sets, so the rule must
read the truth from ``BrokerageRiskPolicy``.

Owner: ``qts.risk.rules.order_spec_validity.OrderSpecValidityRule``.

Forbidden shortcut: letting ``SimulatedExecutionAdapter`` raise
``NotImplementedError`` and surfacing that as the rejection reason.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.orders import OrderType, TimeInForce
from qts.domain.risk import OrderRiskRequest
from qts.risk.rules.order_spec_validity import OrderSpecValidityRule
from qts.strategy_sdk.target import OrderSpec


def _request(order_type: OrderType, **spec_kwargs: Any) -> OrderRiskRequest:
    return OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        order_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        order_spec=OrderSpec(
            order_type=order_type,
            time_in_force=TimeInForce.DAY,
            **spec_kwargs,
        ),
    )


class _SupportedSet:
    """Stand-in for a BrokerageRiskPolicy that only exposes order-type support."""

    def __init__(self, supported: frozenset[OrderType]) -> None:
        self._supported = supported

    @property
    def supported_order_types(self) -> frozenset[OrderType]:
        return self._supported

    @property
    def requires_live_market_data(self) -> bool:
        return False


def test_rule_rejects_order_type_not_in_supported_set() -> None:
    sim_policy = _SupportedSet(
        frozenset(
            {
                OrderType.MARKET,
                OrderType.LIMIT,
                OrderType.STOP,
                OrderType.STOP_LIMIT,
                OrderType.BRACKET,
            }
        )
    )
    rule = OrderSpecValidityRule(brokerage_policy=sim_policy)

    decision = rule.check(_request(OrderType.TRAILING_STOP, trail_amount=Decimal("1")))

    assert decision.approved is False
    assert decision.reason_code == "UNSUPPORTED_ORDER_TYPE"


def test_rule_approves_order_type_in_supported_set() -> None:
    ibkr_policy = _SupportedSet(frozenset(OrderType))
    rule = OrderSpecValidityRule(brokerage_policy=ibkr_policy)

    decision = rule.check(_request(OrderType.TRAILING_STOP, trail_amount=Decimal("1")))

    assert decision.approved is True


def test_rule_without_brokerage_policy_falls_back_to_shape_check() -> None:
    rule = OrderSpecValidityRule()

    market_request = _request(OrderType.MARKET)
    assert rule.check(market_request).approved is True
