"""Performance baselines for hot-path domain primitives.

These benchmarks document the per-call latency of the bottleneck primitives
that show up in every live tick. They are informational (not gating) until
a regression policy is defined in a follow-up item.

Run with: ``uv run pytest tests/benchmarks --benchmark-only``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders import OrderFill, OrderIntent, OrderSide, OrderType
from qts.portfolio.holdings import HoldingBook
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actors.account_actor import AccountActor, ApplyFill
from qts.strategy_sdk.target import OrderSpec

pytestmark = pytest.mark.benchmark


def test_account_actor_apply_fill_baseline(benchmark) -> None:  # type: ignore[no-untyped-def]
    actor = AccountActor(
        initial_cash={"USD": Decimal("1000000")},
        account_id=AccountId("acct-1"),
    )
    instrument = InstrumentId("EQUITY.US.NASDAQ.AAPL")

    counter = {"n": 0}

    def setup() -> tuple[tuple[ApplyFill], dict[str, object]]:
        counter["n"] += 1
        message = ApplyFill(
            fill=OrderFill(
                fill_id=f"f-{counter['n']}",
                order_id=OrderId(f"ord-{counter['n']}"),
                instrument_id=instrument,
                side=OrderSide.BUY if counter["n"] % 2 == 1 else OrderSide.SELL,
                quantity=Decimal("1"),
                price=Decimal("100"),
                account_id=AccountId("acct-1"),
            ),
            currency="USD",
            multiplier=Decimal("1"),
        )
        return (message,), {}

    benchmark.pedantic(actor.handle, setup=setup, rounds=200)


def test_holding_book_apply_fill_baseline(benchmark) -> None:  # type: ignore[no-untyped-def]
    book = HoldingBook()
    instrument = InstrumentId("EQUITY.US.NASDAQ.AAPL")

    def call() -> None:
        book.apply_fill(
            instrument_id=instrument,
            signed_quantity=Decimal("1"),
            price=Decimal("100"),
            multiplier=Decimal("1"),
        )

    benchmark(call)


def test_risk_engine_check_baseline(benchmark) -> None:  # type: ignore[no-untyped-def]
    from qts.domain.risk import OrderRiskRequest

    engine = RiskEngine([MaxNotionalRule(max_notional=Decimal("1000000"))])
    request = OrderRiskRequest(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        quantity=Decimal("1"),
        price=Decimal("100"),
        multiplier=Decimal("1"),
        order_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        order_spec=OrderSpec(order_type=OrderType.MARKET),
    )

    benchmark(engine.check, request)


def test_order_intent_construction_baseline(benchmark) -> None:  # type: ignore[no-untyped-def]
    def call() -> OrderIntent:
        return OrderIntent(
            order_id=OrderId("ord-1"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            account_id=AccountId("acct-1"),
            order_spec=OrderSpec(order_type=OrderType.MARKET),
        )

    benchmark(call)


def test_order_spec_validation_baseline(benchmark) -> None:  # type: ignore[no-untyped-def]
    def call() -> OrderSpec:
        return OrderSpec(
            order_type=OrderType.LIMIT,
            limit_price=Decimal("100.5"),
        )

    benchmark(call)
