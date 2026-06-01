from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar

from tests.support.backtest_streaming import run_engine_streaming

# These tests exercise the actor pipeline (routing, aggregation, timeframe
# aggregation, risk gating), which is independent of fill timing. They pin the
# optimistic same-bar policy so single decision bars fill in place rather than
# deferring under the promotion-grade next_bar_open default.
_SAME_BAR = ExecutionTimingModel.research_only()


def _bar(start: datetime, close: str) -> Bar:
    from qts.core.ids import InstrumentId

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


def test_backtest_engine_runs_strategy_through_execution_flow(tmp_path: Path) -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class BuyOnceStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.has_ordered = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            assert ctx.data.close(self.asset) == bar.close
            if not self.has_ordered:
                ctx.target_quantity(self.asset, Decimal("10"))
                self.has_ordered = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")],
            initial_cash=Decimal("10000"),
        ),
        tmp_path / "execution-flow",
    )
    result = captured.result

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert result.final_account.positions[instrument_id].quantity == Decimal("10")
    assert result.final_account.cash["USD"] == Decimal("9000")
    assert captured.orders[0]["state"] == "filled"
    assert result.processed_bars == 2


def test_backtest_engine_runs_multi_strategy_config_through_shared_aggregation(
    tmp_path: Path,
) -> None:
    from qts.core.ids import AccountId, InstrumentId
    from qts.runtime.config import (
        BacktestMarketDataReference,
        BacktestRuntimeConfig,
        BacktestStrategyConfig,
    )
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class FixedTargetStrategy(Strategy):
        def __init__(self, quantity: Decimal) -> None:
            self.quantity = quantity

        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, self.quantity)

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    runtime_config = BacktestRuntimeConfig(
        roots=("AAPL",),
        symbols=("AAPL",),
        start=start,
        end=start + timedelta(minutes=1),
        timeframe="1m",
        initial_cash=Decimal("10000"),
        instrument_ids={"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")},
        market_data=BacktestMarketDataReference(
            config_path=tmp_path / "historical.yaml",
            catalog="unit",
        ),
        strategies=(
            BacktestStrategyConfig(
                strategy_id="strat-a",
                class_path="tests.FixedTargetStrategy",
                account_id="acct-backtest",
                signal_aggregation_policy="weighted_net",
                signal_weight=Decimal("0.50"),
            ),
            BacktestStrategyConfig(
                strategy_id="strat-b",
                class_path="tests.FixedTargetStrategy",
                account_id="acct-backtest",
                signal_aggregation_policy="weighted_net",
                signal_weight=Decimal("0.50"),
            ),
        ),
    )

    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategies=(
                FixedTargetStrategy(Decimal("10")),
                FixedTargetStrategy(Decimal("20")),
            ),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            backtest_runtime_config=runtime_config,
        ),
        tmp_path / "multi-strategy-aggregation",
    )

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert captured.result.final_account.positions[instrument_id].quantity == Decimal("15")
    assert captured.result.final_account.cash["USD"] == Decimal("8500.00")
    assert captured.manifest["runtime_topology"]["strategy_count"] == 2

    signal_event = next(
        event for event in captured.events if event["kind"] == "runtime.signal_aggregated"
    )
    order_event = next(
        event for event in captured.events if event["kind"] == "runtime.order_submitted"
    )
    assert signal_event["payload"]["contributing_strategy_ids"] == ["strat-a", "strat-b"]
    assert signal_event["payload"]["target_after_aggregation"] == "15.00"
    assert order_event["payload"]["contributing_strategy_ids"] == ["strat-a", "strat-b"]
    assert order_event["account_id"] == AccountId("acct-backtest").value


def test_backtest_engine_target_intents_must_pass_pre_trade_risk_before_order_manager(
    tmp_path: Path,
) -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class OversizedOrderStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("10"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategy=OversizedOrderStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
            risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("999"))]),
        ),
        tmp_path / "risk-rejection",
    )
    result = captured.result

    assert captured.orders == ()
    assert result.final_account.cash["USD"] == Decimal("10000")
    assert result.final_account.positions == {}


def test_backtest_engine_applies_brokerage_model_capabilities(tmp_path: Path) -> None:
    import pytest
    from qts.runtime.config import BacktestMarketDataReference, BacktestRuntimeConfig
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class FractionalFutureStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("1.5"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    runtime_config = BacktestRuntimeConfig(
        roots=("AAPL",),
        symbols=("AAPL",),
        start=start,
        end=start + timedelta(minutes=1),
        timeframe="1m",
        initial_cash=Decimal("10000"),
        strategy_class="tests.FractionalFutureStrategy",
        market_data=BacktestMarketDataReference(
            config_path=tmp_path / "historical.yaml",
            catalog="unit",
        ),
        brokerage_model="IBKR_FUTURES",
    )

    with pytest.raises(ValueError, match="fractional"):
        run_engine_streaming(
            backtest_engine_from_inputs(
                execution_timing=_SAME_BAR,
                strategy=FractionalFutureStrategy(),
                bars=[_bar(start, "100")],
                initial_cash=Decimal("10000"),
                backtest_runtime_config=runtime_config,
            ),
            tmp_path / "brokerage-model",
        )


def test_backtest_engine_routes_bars_through_strategy_actor(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    from qts.backtest import actor_loop as actor_loop_module
    from qts.runtime.actors.strategy_actor import (
        StrategyBarEvent,
        StrategyBarResult,
        StrategyFinalize,
        StrategyFinalized,
    )
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class NoDirectOnBarStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.initialized = True

        def on_bar(self, ctx: Any, bar: object) -> None:
            raise AssertionError("BacktestEngine must route bars through StrategyActor")

    class RecordingStrategyActor:
        seen_bars: list[Bar] = []

        def __init__(self, *, strategy: Strategy, context: Any, result_ref: Any) -> None:
            self.result_ref = result_ref

        def handle(self, message: object) -> None:
            if isinstance(message, StrategyBarEvent):
                self.seen_bars.append(message.bar)
                self.result_ref.tell(StrategyBarResult(bar=message.bar, intents=()))
                return
            if isinstance(message, StrategyFinalize):
                self.result_ref.tell(StrategyFinalized(intents=()))
                return
            raise TypeError(f"unsupported test message: {type(message).__name__}")

    monkeypatch.setattr(actor_loop_module, "StrategyActor", RecordingStrategyActor)

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategy=NoDirectOnBarStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
        ),
        tmp_path / "strategy-actor",
    )

    assert captured.result.processed_bars == 1
    assert RecordingStrategyActor.seen_bars == [_bar(start, "100")]


def test_backtest_engine_routes_strategy_intents_through_signal_aggregator(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    from qts.backtest import actor_loop as actor_loop_module
    from qts.runtime.actors.signal_aggregator_actor import (
        AggregatedSignalBatch,
        StrategySignalEvent,
    )
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class BuyOnceStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.done = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if not self.done:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.done = True

    class RecordingSignalAggregatorActor:
        seen_quantities: list[Decimal] = []

        def __init__(self, *, result_ref: Any) -> None:
            self.result_ref = result_ref

        def handle(self, message: object) -> None:
            if isinstance(message, StrategySignalEvent):
                self.seen_quantities.extend(
                    intent.value for intent in message.intents if intent.value is not None
                )
                self.result_ref.tell(
                    AggregatedSignalBatch(bar=message.bar, intents=message.intents)
                )
                return
            raise TypeError(f"unsupported test message: {type(message).__name__}")

    monkeypatch.setattr(actor_loop_module, "SignalAggregatorActor", RecordingSignalAggregatorActor)

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategy=BuyOnceStrategy(),
            bars=[_bar(start, "100")],
            initial_cash=Decimal("10000"),
        ),
        tmp_path / "signal-aggregator",
    )

    assert RecordingSignalAggregatorActor.seen_quantities == [Decimal("1")]
    assert len(captured.fills) == 1


def test_backtest_engine_streams_source_bars_through_market_data_actor(
    tmp_path: Path,
) -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class BuyOnceStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.has_ordered = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            assert bar.timeframe == "5m"
            assert ctx.data.close(self.asset) == Decimal("104")
            if not self.has_ordered:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.has_ordered = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    source_bars = [
        _bar(start + timedelta(minutes=offset), str(100 + offset)) for offset in range(5)
    ]

    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategy=BuyOnceStrategy(),
            bars=source_bars,
            initial_cash=Decimal("10000"),
            target_timeframe="5m",
            exchange_timezone_by_instrument={instrument_id: UTC},
        ),
        tmp_path / "market-data-actor",
    )
    result = captured.result

    assert result.processed_bars == 1
    assert result.trading_bars == 1
    assert Decimal(captured.fills[0]["price"]) == Decimal("104")
    assert datetime.fromisoformat(captured.trade_ledger[0]["source_bar_time"]) == start


def test_backtest_engine_supports_two_minute_target_timeframe(
    tmp_path: Path,
) -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class BuyOnceStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.has_ordered = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            assert bar.timeframe == "2m"
            assert ctx.data.close(self.asset) == Decimal("101")
            if not self.has_ordered:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.has_ordered = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    source_bars = [_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")]

    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategy=BuyOnceStrategy(),
            bars=source_bars,
            initial_cash=Decimal("10000"),
            target_timeframe="2m",
            exchange_timezone_by_instrument={instrument_id: UTC},
        ),
        tmp_path / "two-minute-market-data",
    )
    result = captured.result

    assert result.processed_bars == 1
    assert result.trading_bars == 1
    assert Decimal(captured.fills[0]["price"]) == Decimal("101")


def test_backtest_engine_uses_strategy_subscription_timeframe_over_config_target(
    tmp_path: Path,
) -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class SubscribedTimeframeStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.has_ordered = False
            ctx.subscribe(self.asset, timeframe="2m", warmup=1)

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            assert bar.timeframe == "2m"
            assert ctx.data.close(self.asset) == Decimal("101")
            if not self.has_ordered:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.has_ordered = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    source_bars = [_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")]

    captured = run_engine_streaming(
        backtest_engine_from_inputs(
            execution_timing=_SAME_BAR,
            strategy=SubscribedTimeframeStrategy(),
            bars=source_bars,
            initial_cash=Decimal("10000"),
            target_timeframe="1m",
            exchange_timezone_by_instrument={instrument_id: UTC},
        ),
        tmp_path / "strategy-subscription-timeframe",
    )
    result = captured.result

    assert result.processed_bars == 1
    assert result.trading_bars == 1
    assert Decimal(captured.fills[0]["price"]) == Decimal("101")
