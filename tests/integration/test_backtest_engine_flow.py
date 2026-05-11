from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.domain.market_data import Bar


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


def test_backtest_engine_runs_strategy_through_execution_flow() -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import Strategy

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
    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")],
        initial_cash=Decimal("10000"),
    ).run()

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert result.final_account.positions[instrument_id].quantity == Decimal("10")
    assert result.final_account.cash["USD"] == Decimal("9000")
    assert result.orders[0].state.value == "filled"
    assert result.processed_bars == 2


def test_backtest_engine_target_intents_must_pass_pre_trade_risk_before_order_manager() -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.strategy_sdk import Strategy

    class OversizedOrderStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("10"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine(
        strategy=OversizedOrderStrategy(),
        bars=[_bar(start, "100")],
        initial_cash=Decimal("10000"),
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("999"))]),
    ).run()

    assert result.orders == ()
    assert result.final_account.cash["USD"] == Decimal("10000")
    assert result.final_account.positions == {}


def test_backtest_engine_routes_bars_through_strategy_actor(monkeypatch: Any) -> None:
    from qts.backtest import engine as engine_module
    from qts.backtest.engine import BacktestEngine
    from qts.runtime.actors.strategy_actor import (
        StrategyBarEvent,
        StrategyBarResult,
        StrategyFinalize,
        StrategyFinalized,
    )
    from qts.strategy_sdk import Strategy

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

    monkeypatch.setattr(engine_module, "StrategyActor", RecordingStrategyActor)

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine(
        strategy=NoDirectOnBarStrategy(),
        bars=[_bar(start, "100")],
        initial_cash=Decimal("10000"),
    ).run()

    assert result.processed_bars == 1
    assert RecordingStrategyActor.seen_bars == [_bar(start, "100")]


def test_backtest_engine_routes_strategy_intents_through_signal_aggregator(
    monkeypatch: Any,
) -> None:
    from qts.backtest import engine as engine_module
    from qts.backtest.engine import BacktestEngine
    from qts.runtime.actors.signal_aggregator_actor import (
        AggregatedSignalBatch,
        StrategySignalEvent,
    )
    from qts.strategy_sdk import Strategy

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

    monkeypatch.setattr(engine_module, "SignalAggregatorActor", RecordingSignalAggregatorActor)

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(start, "100")],
        initial_cash=Decimal("10000"),
    ).run()

    assert RecordingSignalAggregatorActor.seen_quantities == [Decimal("1")]
    assert len(result.fills) == 1


def test_backtest_engine_advances_market_data_events_with_replay_clock(monkeypatch: Any) -> None:
    from collections.abc import Iterable
    from datetime import datetime

    from qts.backtest import engine as engine_module
    from qts.backtest.engine import BacktestEngine
    from qts.strategy_sdk import Strategy

    class HoldStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            pass

        def on_bar(self, ctx: Any, bar: object) -> None:
            pass

    class RecordingReplayClock:
        instances: list[RecordingReplayClock] = []

        def __init__(self, timestamps: Iterable[datetime]) -> None:
            self.timestamps = tuple(sorted(timestamps))
            self.advanced: list[datetime] = []
            self._index = 0
            RecordingReplayClock.instances.append(self)

        def advance(self) -> datetime | None:
            if self._index >= len(self.timestamps):
                return None
            timestamp = self.timestamps[self._index]
            self._index += 1
            self.advanced.append(timestamp)
            return timestamp

    monkeypatch.setattr(engine_module, "ReplayClock", RecordingReplayClock, raising=False)

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine(
        strategy=HoldStrategy(),
        bars=[_bar(start + timedelta(minutes=1), "101"), _bar(start, "100")],
        initial_cash=Decimal("10000"),
    ).run()

    assert result.processed_bars == 2
    assert len(RecordingReplayClock.instances) == 1
    assert RecordingReplayClock.instances[0].advanced == [
        start + timedelta(minutes=1),
        start + timedelta(minutes=2),
    ]


def test_backtest_engine_replay_clock_drives_source_bars_through_market_data_actor() -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import Strategy

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

    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=source_bars,
        initial_cash=Decimal("10000"),
        target_timeframe="5m",
        exchange_timezone_by_instrument={instrument_id: UTC},
    ).run()

    assert result.processed_bars == 1
    assert result.trading_bars == 1
    assert result.fills[0].price == Decimal("104")
    assert result.report.trade_ledger[0].source_bar_time == start
