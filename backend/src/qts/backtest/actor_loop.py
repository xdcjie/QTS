"""Streaming backtest actor loop."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import tzinfo
from decimal import Decimal

from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
from qts.backtest.intent_processor import BacktestProcessedIntent
from qts.backtest.report import EquityCurvePoint
from qts.backtest.sinks import BacktestStreamingSink
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
from qts.runtime.actors.order_manager_actor import OrderManagerActor
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    StrategySignalEvent,
)
from qts.runtime.actors.strategy_actor import (
    StrategyBarEvent,
    StrategyBarResult,
    StrategyFinalize,
    StrategyFinalized,
)
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import PortfolioView, Strategy, StrategyContext
from qts.strategy_sdk.data_view import MarketDataPortal

ProcessIntentHandler = Callable[..., BacktestProcessedIntent]
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
    def _take_strategy_bar_result(mailbox: Mailbox) -> StrategyBarResult:
        """Perform _take_strategy_bar_result."""
        if mailbox.empty():
            raise RuntimeError("strategy actor did not emit a bar result")
        result = mailbox.get()
        if not isinstance(result, StrategyBarResult):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one bar result")
        return result

    @staticmethod
    def _take_signal_batch(mailbox: Mailbox) -> AggregatedSignalBatch:
        """Perform _take_signal_batch."""
        if mailbox.empty():
            raise RuntimeError("signal aggregator actor did not emit a batch")
        result = mailbox.get()
        if not isinstance(result, AggregatedSignalBatch):
            raise TypeError(f"unexpected signal aggregator result: {type(result).__name__}")
        if not mailbox.empty():
            raise RuntimeError("signal aggregator actor emitted more than one batch")
        return result

    @staticmethod
    def _take_strategy_finalized(mailbox: Mailbox) -> StrategyFinalized:
        """Perform _take_strategy_finalized."""
        if mailbox.empty():
            raise RuntimeError("strategy actor did not emit finalization result")
        result = mailbox.get()
        if not isinstance(result, StrategyFinalized):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one finalization result")
        return result

    def _market_data_ref_for(
        self,
        bar: Bar,
        *,
        refs: dict[tuple[str | None, str | tzinfo | None], ActorRef],
        subscriber: ActorRef,
    ) -> ActorRef:
        """Perform _market_data_ref_for."""
        aggregate_timeframe = None
        exchange_timezone: str | tzinfo | None = None
        if self._target_timeframe is not None and bar.timeframe != self._target_timeframe:
            aggregate_timeframe = self._target_timeframe
            try:
                exchange_timezone = self._exchange_timezone_by_instrument[bar.instrument_id]
            except KeyError as exc:
                raise RuntimeError(
                    f"exchange timezone is required to aggregate {bar.instrument_id} "
                    f"from {bar.timeframe} to {self._target_timeframe}"
                ) from exc
        key = (aggregate_timeframe, exchange_timezone)
        ref = refs.get(key)
        if ref is None:
            ref = ActorRef(
                actor=MarketDataActor(
                    subscribers=(subscriber,),
                    aggregate_timeframe=aggregate_timeframe,
                    exchange_timezone=exchange_timezone,
                ),
                mailbox=Mailbox(),
            )
            refs[key] = ref
        return ref

    @staticmethod
    def _history_limit_from_subscriptions(ctx: StrategyContext) -> int | None:
        """Perform _history_limit_from_subscriptions."""
        if not ctx.subscriptions:
            return None
        return max(subscription.warmup for subscription in ctx.subscriptions)

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
        sink: BacktestStreamingSink,
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

        ctx = StrategyContext(
            instrument_registry=self._instrument_registry,
            future_chain_registry=self._future_roll_registry,
        )
        strategy_actor, signal_aggregator_actor = self._resolve_actor_classes()
        strategy_result_mailbox = Mailbox()
        strategy_ref = ActorRef(
            actor=strategy_actor(
                strategy=self._strategy,
                context=ctx,
                result_ref=ActorRef(mailbox=strategy_result_mailbox),
            ),
            mailbox=Mailbox(),
        )
        signal_result_mailbox = Mailbox()
        signal_ref = ActorRef(
            actor=signal_aggregator_actor(result_ref=ActorRef(mailbox=signal_result_mailbox)),
            mailbox=Mailbox(),
        )

        latest_prices: dict[InstrumentId, Decimal] = {}
        warmup_processed = 0
        trading_processed = 0
        event_index = 0
        last_bar: Bar | None = None
        history_limit = self._history_limit_from_subscriptions(ctx) if prune_history else None

        strategy_bars_by_instrument: dict[InstrumentId, list[Bar]] = defaultdict(list)
        market_data_mailbox = Mailbox()
        market_data_subscriber = ActorRef(mailbox=market_data_mailbox)
        market_data_refs: dict[tuple[str | None, str | tzinfo | None], ActorRef] = {}
        for source_bar in self._bars:
            market_data_ref = self._market_data_ref_for(
                source_bar,
                refs=market_data_refs,
                subscriber=market_data_subscriber,
            )
            market_data_ref.tell(MarketDataEvent(payload=source_bar))
            market_data_ref.process_all()
            while not market_data_mailbox.empty():
                payload = market_data_mailbox.get()
                if not isinstance(payload, Bar):
                    raise TypeError(f"unexpected market data payload: {type(payload).__name__}")
                bar = payload
                last_bar = bar
                history = strategy_bars_by_instrument[bar.instrument_id]
                history.append(bar)
                if history_limit is not None and len(history) > history_limit:
                    del history[: len(history) - history_limit]
                portal = MarketDataPortal(strategy_bars_by_instrument)
                latest_prices[bar.instrument_id] = bar.close
                self._update_rolling_prices(
                    bar,
                    latest_prices=latest_prices,
                )
                strategy_ref.tell(
                    StrategyBarEvent(
                        bar=bar,
                        data=portal.data_view(as_of=bar.end_time),
                        portfolio=self._portfolio_view(
                            account_actor.snapshot(),
                            latest_prices=latest_prices,
                        ),
                    )
                )
                strategy_ref.process_all()
                strategy_result = self._take_strategy_bar_result(strategy_result_mailbox)
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

                signal_ref.tell(
                    StrategySignalEvent(
                        bar=bar,
                        intents=strategy_result.intents,
                    )
                )
                signal_ref.process_all()
                signal_batch = self._take_signal_batch(signal_result_mailbox)
                for intent in signal_batch.intents:
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

        strategy_ref.tell(StrategyFinalize())
        strategy_ref.process_all()
        _ = self._take_strategy_finalized(strategy_result_mailbox).intents
        return BacktestActorLoopResult(
            final_account=account_actor.snapshot(),
            warmup_bars=warmup_processed,
            trading_bars=trading_processed,
            last_bar=last_bar,
        )


__all__ = ["BacktestActorLoop", "BacktestActorLoopResult"]
