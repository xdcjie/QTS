from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId
from qts.domain.market_data import Bar
from qts.portfolio.holdings import Holding
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
            bar.instrument_id: Holding(
                instrument_id=bar.instrument_id,
                quantity=Decimal("1"),
                average_cost=Decimal("0"),
                realized_pnl=Decimal("0"),
            )
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
            bar.instrument_id: Holding(
                instrument_id=bar.instrument_id,
                quantity=Decimal("1"),
                average_cost=Decimal("0"),
                realized_pnl=Decimal("0"),
            )
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
            bar.instrument_id: Holding(
                instrument_id=bar.instrument_id,
                quantity=Decimal("1"),
                average_cost=Decimal("0"),
                realized_pnl=Decimal("0"),
            )
        },
        aggregation_decision_id="sigagg-plan",
    )

    assert plans[0].aggregation_decision_id == "sigagg-plan"


def test_order_plan_builder_sizes_continuous_percent_target_with_target_market_price() -> None:
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.registry.future_roll import FutureRollRegistry, FutureRollSelection
    from qts.runtime.intent_processing import OrderPlanBuilder

    signal_bar = Bar(
        instrument_id=InstrumentId("RESEARCH.CARRY.GC"),
        start_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        end_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("0"),
        high=Decimal("0"),
        low=Decimal("0"),
        close=Decimal("0"),
        volume=Decimal("1"),
        is_complete=True,
    )
    concrete_id = InstrumentId("FUTURE.CME.GC.GCG6")
    roll_registry = FutureRollRegistry()
    continuous_id = roll_registry.register_root(
        root_symbol="GC",
        exchange="CME",
        contracts=(concrete_id,),
    )
    roll_registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous_id,
            root_symbol="GC",
            as_of=signal_bar.end_time,
            concrete_instrument_id=concrete_id,
            source_symbol="GCG6",
            prices_by_instrument={concrete_id: Decimal("100")},
        )
    )
    builder = OrderPlanBuilder(
        instrument_context=BacktestInstrumentContext(future_roll_registry=roll_registry)
    )

    plans = builder.build(
        TargetIntent(
            intent_type=TargetIntentType.PERCENT,
            asset=AssetRef(continuous_id, "GC"),
            value=Decimal("0.5"),
        ),
        account_id=AccountId("acct-backtest"),
        bar=signal_bar,
        positions={},
    )

    assert len(plans) == 1
    assert plans[0].instrument_id == concrete_id
    assert plans[0].quantity_delta == Decimal("0.5")
    assert plans[0].market_price == Decimal("100")
