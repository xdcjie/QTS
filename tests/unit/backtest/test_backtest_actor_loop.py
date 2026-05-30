from __future__ import annotations

import inspect
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import BrokerId
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.market_data import Bar
from qts.domain.orders import (
    Order,
    OrderFill,
)
from qts.reporting.backtest import EquityCurvePoint
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.sinks.base import RuntimeEvent
from qts.strategy_sdk import Strategy

from tests.support.backtest_manifest import m1_manifest_kwargs

# Single-bar event-emission tests assert the same-bar fill sequence; pin the
# optimistic policy so the decision bar fills in place instead of deferring
# under the next_bar_open default.
_SAME_BAR_TIMING = ExecutionTimingModel.research_only()


class _RecordingBacktestSink:
    """Collects runtime events without writing artifacts."""

    def __init__(self) -> None:
        """Create an in-memory backtest sink."""
        self.events: list[RuntimeEvent] = []
        self._order_count = 0

    @property
    def order_count(self) -> int:
        """Perform order_count."""
        return self._order_count

    def write(self, event: RuntimeEvent) -> None:
        """Record one runtime event."""
        self.events.append(event)

    def write_processed(
        self, *, orders: tuple[Order, ...], fills: tuple[OrderFill, ...], bar: Bar
    ) -> None:
        """Record processed payload sizes."""
        self._order_count += len(orders)

    def write_equity_point(self, point: EquityCurvePoint) -> None:
        """Ignore equity points in this in-memory sink."""
        del point

    def write_holdings_snapshot(
        self,
        *,
        gross_notional: object,
        net_notional: object,
    ) -> None:
        """Ignore holdings notional snapshots in this in-memory sink."""
        del gross_notional, net_notional

    def write_account_snapshot(self, point: AccountSnapshot) -> None:
        """Ignore account snapshots in this in-memory sink."""
        del point


def test_backtest_actor_loop_run_is_named_phase_orchestrator() -> None:
    from qts.backtest.actor_loop import BacktestActorLoop

    required_phases = (
        "initialize_run_phase",
        "process_market_data_phase",
        "process_warmup_phase",
        "process_trading_phase",
        "finalize_run_phase",
    )

    for phase in required_phases:
        method = getattr(BacktestActorLoop, phase, None)
        assert method is not None, f"missing backtest actor-loop phase: {phase}"

    source_lines = inspect.getsourcelines(BacktestActorLoop.run)[0]
    assert len(source_lines) <= 80


def _bar(start: datetime, close: str = "100") -> Bar:
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


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def test_backtest_actor_loop_processes_bars_and_returns_runtime_result(tmp_path: Path) -> None:
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
    from qts.backtest.engine import BacktestCostModel
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.backtest.portfolio_projection import BacktestPortfolioProjector
    from qts.core.ids import AccountId, BrokerId, InstrumentId, RuntimeRunId, StrategyId
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.reporting.backtest import BacktestArtifactWriter
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.intent_processing import TargetIntentProcessor
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEventContext

    class OneOrderStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.placed = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if not self.placed:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.placed = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start, "100"), _bar(start + timedelta(minutes=1), "101")]
    strategy = OneOrderStrategy()
    instrument_context = BacktestInstrumentContext(
        instrument_registry=None,
        registry_bars=bars,
    )
    portfolio_projector = BacktestPortfolioProjector()
    intent_processor = TargetIntentProcessor(
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("1000000"))]),
        instrument_context=instrument_context,
        multiplier_for=portfolio_projector.multiplier_for,
        broker_id=BrokerId("simulated"),
    )

    loop = BacktestActorLoop(
        strategy=strategy,
        bars=bars,
        config=BacktestActorLoopConfig(initial_cash=Decimal("10000"), warmup_bars=0),
        dependencies=BacktestActorLoopDependencies(
            instrument_registry=instrument_context.instrument_registry(),
            contract_multipliers={},
            execution_adapter=SimulatedExecutionAdapter(BacktestCostModel()),
            process_intent=intent_processor.process_intent,
            portfolio_view=portfolio_projector.portfolio_view,
            equity_point=portfolio_projector.equity_point,
            update_rolling_prices=instrument_context.update_rolling_prices,
        ),
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
    )
    writer = BacktestArtifactWriter(tmp_path)
    sink = BacktestRuntimeEventSink(
        writer,
        context=RuntimeEventContext(
            run_id=RuntimeRunId("bt-actor-loop"),
            mode="backtest",
            execution_environment="simulated",
            account_id=AccountId("acct-backtest"),
            strategy_id=StrategyId("strategy-backtest"),
        ),
    )
    runtime = loop.run(sink=sink, prune_history=True, compact_orders=True)

    writer.finalize(
        config_hash="cfg",
        **m1_manifest_kwargs(),
        cost_model={},
        processed_bars=runtime.processed_bars,
        warmup_bars=runtime.warmup_bars,
        trading_bars=runtime.trading_bars,
        final_cash=runtime.final_account.cash["USD"],
        strategy_version="test",
    )

    assert runtime.processed_bars == 2
    assert runtime.trading_bars == 2
    assert runtime.warmup_bars == 0
    assert runtime.final_account.positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    assert sink.order_count == 1


def test_backtest_actor_loop_emits_signal_events() -> None:
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
    from qts.backtest.engine import BacktestCostModel
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.backtest.portfolio_projection import BacktestPortfolioProjector
    from qts.core.ids import AccountId, StrategyId
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.intent_processing import TargetIntentProcessor

    class OneOrderStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.placed = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if not self.placed:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.placed = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start, "100")]
    strategy = OneOrderStrategy()
    instrument_context = BacktestInstrumentContext(
        instrument_registry=None, registry_bars=bars, execution_timing=_SAME_BAR_TIMING
    )
    portfolio_projector = BacktestPortfolioProjector()
    intent_processor = TargetIntentProcessor(
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("1000000"))]),
        instrument_context=instrument_context,
        multiplier_for=portfolio_projector.multiplier_for,
        broker_id=BrokerId("simulated"),
    )

    loop = BacktestActorLoop(
        strategy=strategy,
        bars=bars,
        config=BacktestActorLoopConfig(initial_cash=Decimal("10000"), warmup_bars=0),
        dependencies=BacktestActorLoopDependencies(
            instrument_registry=instrument_context.instrument_registry(),
            contract_multipliers={},
            execution_adapter=SimulatedExecutionAdapter(BacktestCostModel()),
            process_intent=intent_processor.process_intent,
            portfolio_view=portfolio_projector.portfolio_view,
            equity_point=portfolio_projector.equity_point,
            update_rolling_prices=instrument_context.update_rolling_prices,
            execution_timing=_SAME_BAR_TIMING,
        ),
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
    )
    sink = _RecordingBacktestSink()
    loop.run(sink=sink, prune_history=True, compact_orders=True)

    kinds = [event.kind for event in sink.events]
    assert kinds == [
        "runtime.market_data",
        "runtime.signal_received",
        "runtime.strategy_intent",
        "runtime.signal_aggregated",
        "runtime.risk_decision",
        "runtime.order_submitted",
        "runtime.broker_report",
        "runtime.fill_applied",
        "runtime.account_snapshot",
    ]
    order_event = next(event for event in sink.events if event.kind == "runtime.order_submitted")
    broker_event = next(event for event in sink.events if event.kind == "runtime.broker_report")
    fill_event = next(event for event in sink.events if event.kind == "runtime.fill_applied")
    assert order_event.payload["client_order_id"] == "bt-client-000001"
    assert broker_event.payload["client_order_id"] == "bt-client-000001"
    assert fill_event.payload["client_order_id"] == "bt-client-000001"
    assert fill_event.payload["order_id"] == "bt-000001"
    assert fill_event.correlation_id == order_event.correlation_id


def test_backtest_actor_loop_emits_broker_reject_event_for_capability_reject(
    tmp_path: Path,
) -> None:
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
    from qts.backtest.engine import BacktestCostModel
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.backtest.portfolio_projection import BacktestPortfolioProjector
    from qts.core.ids import AccountId, BrokerId, RuntimeRunId, StrategyId
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.execution.broker import BrokerCapabilities
    from qts.reporting.backtest import BacktestArtifactWriter
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.intent_processing import TargetIntentProcessor
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEventContext

    class OneOrderStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("1"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start, "100")]
    instrument_context = BacktestInstrumentContext(
        instrument_registry=None, registry_bars=bars, execution_timing=_SAME_BAR_TIMING
    )
    portfolio_projector = BacktestPortfolioProjector()
    intent_processor = TargetIntentProcessor(
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("1000000"))]),
        instrument_context=instrument_context,
        multiplier_for=portfolio_projector.multiplier_for,
        broker_id=BrokerId("simulated"),
    )
    loop = BacktestActorLoop(
        strategy=OneOrderStrategy(),
        bars=bars,
        config=BacktestActorLoopConfig(initial_cash=Decimal("10000"), warmup_bars=0),
        dependencies=BacktestActorLoopDependencies(
            instrument_registry=instrument_context.instrument_registry(),
            contract_multipliers={},
            execution_adapter=SimulatedExecutionAdapter(
                BacktestCostModel(),
                capabilities=BrokerCapabilities(
                    broker_id=BrokerId("simulated"),
                    supports_market_orders=False,
                ),
            ),
            process_intent=intent_processor.process_intent,
            portfolio_view=portfolio_projector.portfolio_view,
            equity_point=portfolio_projector.equity_point,
            update_rolling_prices=instrument_context.update_rolling_prices,
            execution_timing=_SAME_BAR_TIMING,
        ),
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
    )
    writer = BacktestArtifactWriter(tmp_path, run_id=RuntimeRunId("bt-capability-reject"))
    sink = BacktestRuntimeEventSink(
        writer,
        context=RuntimeEventContext(
            run_id=RuntimeRunId("bt-capability-reject"),
            mode="backtest",
            execution_environment="simulated",
            account_id=AccountId("acct-backtest"),
            strategy_id=StrategyId("strategy-backtest"),
        ),
    )

    runtime = loop.run(sink=sink, prune_history=True, compact_orders=True)
    writer.finalize(
        config_hash="cfg",
        **m1_manifest_kwargs(),
        cost_model={},
        processed_bars=runtime.processed_bars,
        warmup_bars=runtime.warmup_bars,
        trading_bars=runtime.trading_bars,
        final_cash=runtime.final_account.cash["USD"],
        strategy_version="test",
    )

    rows = _read_ndjson(next(tmp_path.glob("*.events.ndjson")))
    event_kinds = [row["kind"] for row in rows]
    assert "runtime.broker_rejected" in event_kinds, (
        f"broker_rejected not found in event kinds: {event_kinds}"
    )
    reject_event = next(row for row in rows if row["kind"] == "runtime.broker_rejected")
    assert reject_event["payload"]["reason_code"] == "unsupported_order_type"
    assert reject_event["payload"]["broker_capability_model"]["supports_market_orders"] is False
    assert "runtime.fill_applied" not in [row["kind"] for row in rows]
    assert runtime.final_account.positions == {}
    assert runtime.final_account.cash["USD"] == Decimal("10000")


def test_backtest_actor_loop_emits_market_data_provenance() -> None:
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
    from qts.backtest.engine import BacktestCostModel
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.backtest.portfolio_projection import BacktestPortfolioProjector
    from qts.core.ids import AccountId, StrategyId
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.intent_processing import TargetIntentProcessor

    class NoopStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            return None

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start, "100")]
    instrument_context = BacktestInstrumentContext(instrument_registry=None, registry_bars=bars)
    portfolio_projector = BacktestPortfolioProjector()
    intent_processor = TargetIntentProcessor(
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("1000000"))]),
        instrument_context=instrument_context,
        multiplier_for=portfolio_projector.multiplier_for,
        broker_id=BrokerId("simulated"),
    )
    loop = BacktestActorLoop(
        strategy=NoopStrategy(),
        bars=bars,
        config=BacktestActorLoopConfig(initial_cash=Decimal("10000"), warmup_bars=0),
        dependencies=BacktestActorLoopDependencies(
            instrument_registry=instrument_context.instrument_registry(),
            contract_multipliers={},
            execution_adapter=SimulatedExecutionAdapter(BacktestCostModel()),
            process_intent=intent_processor.process_intent,
            portfolio_view=portfolio_projector.portfolio_view,
            equity_point=portfolio_projector.equity_point,
            update_rolling_prices=instrument_context.update_rolling_prices,
            market_data_provenance_for=lambda bar: {
                "source_id": "local_historical",
                "dataset_id": "dataset-a",
                "provider": "csv",
                "permission_state": None,
                "adjustment_mode": "raw",
                "content_hash": "sha256:abc",
                "row_count": 1,
            },
        ),
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
    )
    sink = _RecordingBacktestSink()

    loop.run(sink=sink, prune_history=True, compact_orders=True)

    market_data_event = next(event for event in sink.events if event.kind == "runtime.market_data")
    assert market_data_event.payload["dataset_id"] == "dataset-a"
    assert market_data_event.payload["source_id"] == "local_historical"


def test_backtest_actor_loop_emits_conflict_reject_events_when_policy_rejects() -> None:
    from qts.backtest.actor_loop import BacktestActorLoop
    from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
    from qts.backtest.engine import BacktestCostModel
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.backtest.portfolio_projection import BacktestPortfolioProjector
    from qts.core.ids import AccountId, StrategyId
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.intent_processing import TargetIntentProcessor

    class ConflictStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("1"))
            ctx.target_quantity(self.asset, Decimal("-1"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start, "100")]
    strategy = ConflictStrategy()
    instrument_context = BacktestInstrumentContext(instrument_registry=None, registry_bars=bars)
    portfolio_projector = BacktestPortfolioProjector()
    intent_processor = TargetIntentProcessor(
        risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("1000000"))]),
        instrument_context=instrument_context,
        multiplier_for=portfolio_projector.multiplier_for,
        broker_id=BrokerId("simulated"),
    )

    loop = BacktestActorLoop(
        strategy=strategy,
        bars=bars,
        config=BacktestActorLoopConfig(initial_cash=Decimal("10000"), warmup_bars=0),
        dependencies=BacktestActorLoopDependencies(
            instrument_registry=instrument_context.instrument_registry(),
            contract_multipliers={},
            execution_adapter=SimulatedExecutionAdapter(BacktestCostModel()),
            process_intent=intent_processor.process_intent,
            portfolio_view=portfolio_projector.portfolio_view,
            equity_point=portfolio_projector.equity_point,
            update_rolling_prices=instrument_context.update_rolling_prices,
        ),
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strat-backtest-conflict"),
        signal_aggregation_policy="reject_conflict",
    )
    sink = _RecordingBacktestSink()
    loop.run(sink=sink, prune_history=True, compact_orders=True)

    kinds = [event.kind for event in sink.events]
    assert "runtime.signal_conflict_detected" in kinds
    assert "runtime.signal_rejected" in kinds
    assert "runtime.order_submitted" not in kinds
    assert sink.order_count == 0
