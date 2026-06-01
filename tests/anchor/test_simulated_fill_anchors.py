"""Anchor: simulated execution only fills when the bar's price range crosses limit/stop.

Domain fact: a LIMIT BUY at price L fills only when the bar's low traded at or
below L; a LIMIT SELL at L fills only when the bar's high traded at or above L;
a STOP BUY at S triggers only when the bar's high reached S; a STOP SELL at S
triggers only when the bar's low reached S. STOP_LIMIT requires the stop side
to trigger and the resulting limit side to be marketable in the same bar.

Owner: ``SimulatedExecutionAdapter.execute_market_order`` (it receives a
``market_price`` equal to the bar close; the bar's high/low travel through the
existing ``bar_high`` / ``bar_low`` parameters added for OPT-27.1).

Forbidden shortcut: returning ``spec.limit_price`` or ``spec.stop_price``
unconditionally as the fill price.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
    OrderType,
    TimeInForce,
)
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.strategy_sdk.target import OrderSpec


@dataclass(frozen=True, slots=True)
class _FixedCost:
    fixed_commission_per_contract: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")


def _make_adapter() -> SimulatedExecutionAdapter:
    return SimulatedExecutionAdapter(cost_model=_FixedCost())


def _intent(side: str, *, order_type: OrderType, **spec_kwargs: Any) -> OrderIntent:
    return OrderIntent(
        order_id=OrderId("ord-1"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
        quantity=Decimal("1"),
        account_id=AccountId("acct-1"),
        order_spec=OrderSpec(
            order_type=order_type,
            time_in_force=TimeInForce.DAY,
            **spec_kwargs,
        ),
    )


def _execute(
    adapter: SimulatedExecutionAdapter,
    intent: OrderIntent,
    *,
    market_price: Decimal,
    bar_high: Decimal,
    bar_low: Decimal,
) -> ExecutionReport:
    return adapter.execute_market_order(
        intent,
        broker_order_id="bo-1",
        market_price=market_price,
        bar_high=bar_high,
        bar_low=bar_low,
        account_id=AccountId("acct-1"),
        strategy_id=StrategyId("strat-1"),
        client_order_id="cli-1",
        correlation_id=CorrelationId("corr-1"),
    )


# ---------- LIMIT BUY ----------


def test_limit_buy_fills_when_bar_traded_at_or_below_limit() -> None:
    intent = _intent("buy", order_type=OrderType.LIMIT, limit_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("99"),
        bar_high=Decimal("101"),
        bar_low=Decimal("98"),
    )
    assert report.status is ExecutionReportStatus.FILLED
    assert report.fill_price == Decimal("100")


def test_limit_buy_does_not_fill_when_bar_stays_above_limit() -> None:
    intent = _intent("buy", order_type=OrderType.LIMIT, limit_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("102"),
        bar_high=Decimal("103"),
        bar_low=Decimal("101"),
    )
    assert report.status is ExecutionReportStatus.ACCEPTED
    assert report.filled_quantity == Decimal("0")


def test_limit_buy_fills_on_gap_down_below_limit() -> None:
    intent = _intent("buy", order_type=OrderType.LIMIT, limit_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("95"),
        bar_high=Decimal("96"),
        bar_low=Decimal("94"),
    )
    assert report.status is ExecutionReportStatus.FILLED
    assert report.fill_price == Decimal("96")


# ---------- LIMIT SELL ----------


def test_limit_sell_fills_when_bar_traded_at_or_above_limit() -> None:
    intent = _intent("sell", order_type=OrderType.LIMIT, limit_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("101"),
        bar_high=Decimal("102"),
        bar_low=Decimal("99"),
    )
    assert report.status is ExecutionReportStatus.FILLED
    assert report.fill_price == Decimal("100")


def test_limit_sell_does_not_fill_when_bar_stays_below_limit() -> None:
    intent = _intent("sell", order_type=OrderType.LIMIT, limit_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("98"),
        bar_high=Decimal("99"),
        bar_low=Decimal("97"),
    )
    assert report.status is ExecutionReportStatus.ACCEPTED
    assert report.filled_quantity == Decimal("0")


# ---------- STOP BUY ----------


def test_stop_buy_triggers_when_bar_high_reaches_stop() -> None:
    intent = _intent("buy", order_type=OrderType.STOP, stop_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("100.5"),
        bar_high=Decimal("101"),
        bar_low=Decimal("99"),
    )
    assert report.status is ExecutionReportStatus.FILLED
    assert report.fill_price == Decimal("100")


def test_stop_buy_does_not_trigger_when_bar_stays_below_stop() -> None:
    intent = _intent("buy", order_type=OrderType.STOP, stop_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("98"),
        bar_high=Decimal("99"),
        bar_low=Decimal("97"),
    )
    assert report.status is ExecutionReportStatus.ACCEPTED


def test_stop_buy_uses_gap_open_as_fill_price() -> None:
    intent = _intent("buy", order_type=OrderType.STOP, stop_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("106"),
        bar_high=Decimal("107"),
        bar_low=Decimal("105"),
    )
    assert report.status is ExecutionReportStatus.FILLED
    assert report.fill_price == Decimal("105")


# ---------- STOP SELL ----------


def test_stop_sell_triggers_when_bar_low_reaches_stop() -> None:
    intent = _intent("sell", order_type=OrderType.STOP, stop_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("99.5"),
        bar_high=Decimal("101"),
        bar_low=Decimal("99"),
    )
    assert report.status is ExecutionReportStatus.FILLED
    assert report.fill_price == Decimal("100")


def test_stop_sell_does_not_trigger_when_bar_stays_above_stop() -> None:
    intent = _intent("sell", order_type=OrderType.STOP, stop_price=Decimal("100"))
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("102"),
        bar_high=Decimal("103"),
        bar_low=Decimal("101"),
    )
    assert report.status is ExecutionReportStatus.ACCEPTED


# ---------- STOP_LIMIT ----------


def test_stop_limit_buy_requires_stop_trigger_and_marketable_limit() -> None:
    intent = _intent(
        "buy",
        order_type=OrderType.STOP_LIMIT,
        stop_price=Decimal("100"),
        limit_price=Decimal("100.5"),
    )
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("100.25"),
        bar_high=Decimal("100.6"),
        bar_low=Decimal("99.8"),
    )
    assert report.status is ExecutionReportStatus.FILLED
    assert report.fill_price == Decimal("100.5")


def test_stop_limit_buy_holds_when_stop_triggered_but_limit_not_marketable() -> None:
    intent = _intent(
        "buy",
        order_type=OrderType.STOP_LIMIT,
        stop_price=Decimal("100"),
        limit_price=Decimal("100.3"),
    )
    report = _execute(
        _make_adapter(),
        intent,
        market_price=Decimal("101"),
        bar_high=Decimal("101.5"),
        bar_low=Decimal("100.8"),
    )
    assert report.status is ExecutionReportStatus.ACCEPTED


# ---------- TRAILING_STOP / MOO / MOC / ICEBERG are unsupported in sim ----------


def test_simulated_adapter_rejects_unsupported_order_types() -> None:
    # After OPT-27.2 the simulated brokerage declares these types as
    # unsupported in its capability matrix, so the adapter emits structured
    # rejected reports instead of throwing from the actor hot path.
    for unsupported in (
        OrderType.TRAILING_STOP,
        OrderType.MARKET_ON_OPEN,
        OrderType.MARKET_ON_CLOSE,
        OrderType.ICEBERG,
    ):
        intent_kwargs: dict[str, Decimal] = {}
        if unsupported is OrderType.TRAILING_STOP:
            intent_kwargs["trail_amount"] = Decimal("1")
        intent = _intent("buy", order_type=unsupported, **intent_kwargs)
        report = _execute(
            _make_adapter(),
            intent,
            market_price=Decimal("100"),
            bar_high=Decimal("101"),
            bar_low=Decimal("99"),
        )
        assert report.status is ExecutionReportStatus.REJECTED
        assert report.reason_code == "UNSUPPORTED_ORDER_TYPE"
        assert (
            report.failure_reason
            == f"simulated execution does not support {unsupported.value} orders"
        )
