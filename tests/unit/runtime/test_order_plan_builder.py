from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId
from qts.domain.market_data import Bar
from qts.portfolio.position_book import Position
from qts.strategy_sdk import TargetIntent, TargetIntentType
from qts.strategy_sdk.asset_ref import AssetRef


def _bar(start: datetime, close: str = "100") -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def _asset() -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        symbol="AAPL",
    )


def test_order_plan_builder_converts_quantity_target_to_delta_plan() -> None:
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.runtime.intent_processing import OrderPlanBuilder

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    builder = OrderPlanBuilder(instrument_context=BacktestInstrumentContext(registry_bars=(bar,)))

    plans = builder.build(
        TargetIntent(intent_type=TargetIntentType.QUANTITY, asset=_asset(), value=Decimal("3")),
        account_id=AccountId("acct-backtest"),
        bar=bar,
        positions={
            bar.instrument_id: Position(instrument_id=bar.instrument_id, quantity=Decimal("1"))
        },
    )

    assert len(plans) == 1
    assert plans[0].account_id == AccountId("acct-backtest")
    assert plans[0].instrument_id == bar.instrument_id
    assert plans[0].quantity_delta == Decimal("2")
    assert plans[0].market_price == Decimal("100")
    assert plans[0].order_time == bar.end_time


def test_order_plan_builder_returns_no_plan_when_target_already_matches_position() -> None:
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.runtime.intent_processing import OrderPlanBuilder

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    builder = OrderPlanBuilder(instrument_context=BacktestInstrumentContext(registry_bars=(bar,)))

    plans = builder.build(
        TargetIntent(intent_type=TargetIntentType.QUANTITY, asset=_asset(), value=Decimal("1")),
        account_id=AccountId("acct-backtest"),
        bar=bar,
        positions={
            bar.instrument_id: Position(instrument_id=bar.instrument_id, quantity=Decimal("1"))
        },
    )

    assert plans == ()


def test_order_plan_builder_carries_aggregation_decision_id() -> None:
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.runtime.intent_processing import OrderPlanBuilder

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    builder = OrderPlanBuilder(instrument_context=BacktestInstrumentContext(registry_bars=(bar,)))

    plans = builder.build(
        TargetIntent(intent_type=TargetIntentType.QUANTITY, asset=_asset(), value=Decimal("3")),
        account_id=AccountId("acct-backtest"),
        bar=bar,
        positions={
            bar.instrument_id: Position(instrument_id=bar.instrument_id, quantity=Decimal("1"))
        },
        aggregation_decision_id="sigagg-plan",
    )

    assert plans[0].aggregation_decision_id == "sigagg-plan"
