"""Streaming backtest actor loop."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal

from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.reporting.backtest import EquityCurvePoint
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor
from qts.runtime.intent_processing import ProcessedIntent
from qts.runtime.mailbox import Mailbox
from qts.runtime.market_data_flow import MarketDataFlow
from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline
from qts.strategy_sdk import PortfolioView, Strategy

ProcessIntentHandler = Callable[..., ProcessedIntent]
PortfolioViewBuilder = Callable[..., PortfolioView]
EquityPointBuilder = Callable[..., EquityCurvePoint]
RollingPriceUpdater = Callable[..., None]


@dataclass(frozen=True, slots=True)
class BacktestActorLoopResult:
    """Result summary produced by an actor loop run."""

    final_account: AccountSnapshot
    warmup_bars: int
    trading_bars: int
    last_bar: Bar | None

    @property
    def processed_bars(self) -> int:
        """Perform processed_bars."""
        return self.warmup_bars + self.trading_bars


class BacktestActorLoop:
    """Run backtest bars through strategy/order execution actors."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        bars: Iterable[Bar],
        config: BacktestActorLoopConfig,
        dependencies: BacktestActorLoopDependencies,
    ) -> None:
        """Perform __init__."""
        self._strategy = strategy
        self._bars = bars
        self._initial_cash = config.initial_cash
        self._target_timeframe = config.target_timeframe
        self._exchange_timezone_by_instrument = dict(dependencies.exchange_timezone_by_instrument)
        self._warmup_bars = config.warmup_bars
        self._instrument_registry = dependencies.instrument_registry
        self._future_roll_registry = dependencies.future_roll_registry
        self._contract_multipliers = dict(dependencies.contract_multipliers)
        self._execution_adapter = dependencies.execution_adapter
        self._process_intent = dependencies.process_intent
        self._portfolio_view = dependencies.portfolio_view
        self._equity_point = dependencies.equity_point
        self._update_rolling_prices = dependencies.update_rolling_prices

    @staticmethod
    def _resolve_actor_classes() -> tuple[type, type]:
        """Perform _resolve_actor_classes."""
        from qts.backtest import engine as engine_module

        strategy_actor = engine_module.StrategyActor
        signal_aggregator_actor = engine_module.SignalAggregatorActor
        return strategy_actor, signal_aggregator_actor

    def run(
        self,
        *,
        sink: BacktestRuntimeEventSink,
        prune_history: bool,
        compact_orders: bool,
    ) -> BacktestActorLoopResult:
        """Perform run."""
        account_actor = AccountActor(initial_cash={"USD": self._initial_cash})
        account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
        execution_mailbox = Mailbox()
        order_manager_mailbox = Mailbox()
        order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=execution_mailbox),
            account_ref=account_ref,
            multiplier_by_instrument=self._contract_multipliers,
        )
        order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
        execution_ref = ActorRef(
            actor=ExecutionActor(
                order_manager_ref=order_manager_ref,
                execution_adapter=self._execution_adapter,
            ),
            mailbox=execution_mailbox,
        )

        strategy_actor, signal_aggregator_actor = self._resolve_actor_classes()
        strategy_pipeline = StrategyExecutionPipeline(
            strategy=self._strategy,
            instrument_registry=self._instrument_registry,
            future_chain_registry=self._future_roll_registry,
            portfolio_view=self._portfolio_view,
            prune_history=prune_history,
            strategy_actor_type=strategy_actor,
            signal_aggregator_actor_type=signal_aggregator_actor,
        )

        latest_prices: dict[InstrumentId, Decimal] = {}
        warmup_processed = 0
        trading_processed = 0
        event_index = 0
        last_bar: Bar | None = None

        market_data_flow = MarketDataFlow(
            target_timeframe=self._target_timeframe,
            exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
        )
        for source_bar in self._bars:
            for bar in market_data_flow.publish_bar(source_bar):
                last_bar = bar
                latest_prices[bar.instrument_id] = bar.close
                self._update_rolling_prices(
                    bar,
                    latest_prices=latest_prices,
                )
                strategy_result = strategy_pipeline.execute_bar(
                    bar,
                    account_snapshot=account_actor.snapshot(),
                    latest_prices=latest_prices,
                    aggregate_signals=event_index >= self._warmup_bars,
                )
                if event_index < self._warmup_bars:
                    warmup_processed += 1
                    sink.write_equity_point(
                        self._equity_point(
                            bar,
                            account_actor.snapshot(),
                            latest_prices=latest_prices,
                        )
                    )
                    event_index += 1
                    continue

                for intent in strategy_result.intents:
                    processed = self._process_intent(
                        intent,
                        bar=bar,
                        account_actor=account_actor,
                        order_manager_actor=order_manager_actor,
                        order_manager_ref=order_manager_ref,
                        execution_ref=execution_ref,
                        account_ref=account_ref,
                        order_number=sink.order_count + 1,
                    )
                    order_payload = processed.orders
                    fill_payload = processed.fills
                    sink.write_processed(
                        orders=order_payload,
                        fills=fill_payload,
                        bar=bar,
                    )
                    if compact_orders:
                        order_manager_actor.compact_for_streaming(
                            order.order_id for order in order_payload
                        )
                trading_processed += 1
                sink.write_equity_point(
                    self._equity_point(
                        bar,
                        account_actor.snapshot(),
                        latest_prices=latest_prices,
                    )
                )
                event_index += 1

        _ = strategy_pipeline.finalize()
        return BacktestActorLoopResult(
            final_account=account_actor.snapshot(),
            warmup_bars=warmup_processed,
            trading_bars=trading_processed,
            last_bar=last_bar,
        )


__all__ = ["BacktestActorLoop", "BacktestActorLoopResult"]
