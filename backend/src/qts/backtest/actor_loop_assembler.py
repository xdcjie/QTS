"""Backtest run-topology assembly."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from types import SimpleNamespace
from typing import TYPE_CHECKING, TypeAlias

from qts.backtest.dependencies import BacktestActorLoopConfig, BacktestActorLoopDependencies
from qts.core.ids import AccountId, StrategyId
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import (
    AccountActor,
)
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import (
    OrderManagerActor,
)
from qts.runtime.broker_runtime_topology import StrategyRuntimeBinding
from qts.runtime.mailbox import Mailbox
from qts.runtime.market_data_flow import MarketDataFlow
from qts.runtime.runtime_event_writer import RuntimeEventWriter
from qts.runtime.signal_policy import SignalAggregationPolicy
from qts.runtime.strategy_execution_pipeline import (
    StrategyExecutionPipeline,
    StrategyExecutionResult,
)
from qts.runtime.topology import StrategyRuntimeSpec
from qts.strategy_sdk import Strategy

if TYPE_CHECKING:
    from qts.backtest.actor_loop import BacktestRuntimeSink

BacktestActorLoopState: TypeAlias = SimpleNamespace
BacktestStrategyExecution: TypeAlias = tuple[StrategyRuntimeBinding, StrategyExecutionResult]
BacktestStrategyBarExecution: TypeAlias = tuple[BacktestStrategyExecution, ...]


class BacktestActorLoopAssembler:
    """Build the backtest run's actor topology, strategy bindings, and run state."""

    def __init__(
        self,
        *,
        config: BacktestActorLoopConfig,
        dependencies: BacktestActorLoopDependencies,
        strategies: tuple[Strategy, ...],
        strategy_specs: tuple[StrategyRuntimeSpec, ...],
        account_id: AccountId,
    ) -> None:
        """Bind the assembler to the run's config, dependencies, strategies, and account."""
        self._initial_cash = config.initial_cash
        self._target_timeframe = config.target_timeframe
        self._exchange_timezone_by_instrument = dict(dependencies.exchange_timezone_by_instrument)
        self._session_window_by_instrument = dict(dependencies.session_window_by_instrument)
        self._instrument_registry = dependencies.instrument_registry
        self._future_roll_registry = dependencies.future_roll_registry
        self._contract_multipliers = dict(dependencies.contract_multipliers)
        self._execution_adapter = dependencies.execution_adapter
        self._portfolio_view = dependencies.portfolio_view
        self._strategies = strategies
        self._strategy_specs = strategy_specs
        self._account_id = account_id

    def initialize_run_phase(
        self,
        *,
        sink: BacktestRuntimeSink,
        prune_history: bool,
        compact_orders: bool,
        strategy_actor: type,
        signal_aggregator_actor: type,
    ) -> BacktestActorLoopState:
        """Initialize actors, pipeline, market-data flow, and run state."""
        account_actor = AccountActor(
            initial_cash={"USD": self._initial_cash},
            account_id=self._account_id,
        )
        account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
        execution_mailbox = Mailbox()
        order_manager_mailbox = Mailbox()
        order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=execution_mailbox),
            account_ref=account_ref,
            multiplier_by_instrument=self._contract_multipliers,
            account_id=self._account_id,
        )
        order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
        execution_ref = ActorRef(
            actor=ExecutionActor(
                order_manager_ref=order_manager_ref,
                execution_adapter=self._execution_adapter,
            ),
            mailbox=execution_mailbox,
        )
        event_writer = RuntimeEventWriter(write=sink.write)

        strategy_bindings = self.build_strategy_bindings(
            prune_history=prune_history,
            strategy_actor=strategy_actor,
            signal_aggregator_actor=signal_aggregator_actor,
        )
        signal_result_mailbox = Mailbox()
        signal_aggregator_ref = ActorRef(
            actor=signal_aggregator_actor(
                result_ref=ActorRef(mailbox=signal_result_mailbox),
            ),
            mailbox=Mailbox(),
        )
        target_timeframe = self._strategy_subscription_target_timeframe(
            tuple(binding.pipeline for binding in strategy_bindings),
            fallback=self._target_timeframe,
        )

        market_data_flow = MarketDataFlow(
            target_timeframe=target_timeframe,
            exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
            session_window_by_instrument=self._session_window_by_instrument,
        )
        return BacktestActorLoopState(
            sink=sink,
            compact_orders=compact_orders,
            account_ref=account_ref,
            order_manager_ref=order_manager_ref,
            execution_ref=execution_ref,
            event_writer=event_writer,
            strategy_bindings=strategy_bindings,
            signal_aggregator_ref=signal_aggregator_ref,
            signal_result_mailbox=signal_result_mailbox,
            market_data_flow=market_data_flow,
            latest_prices={},
            pending_fills={},
            warmup_processed=0,
            trading_processed=0,
            event_index=0,
            last_bar=None,
        )

    def build_strategy_bindings(
        self,
        *,
        prune_history: bool,
        strategy_actor: type,
        signal_aggregator_actor: type,
    ) -> tuple[StrategyRuntimeBinding, ...]:
        """Build strategy execution pipelines from normalized backtest specs."""
        bindings: list[StrategyRuntimeBinding] = []
        for strategy, spec in zip(self._strategies, self._strategy_specs, strict=True):
            pipeline = StrategyExecutionPipeline(
                strategy=strategy,
                instrument_registry=self._instrument_registry,
                future_chain_registry=self._future_roll_registry,
                portfolio_view=self._portfolio_view,
                prune_history=prune_history,
                strategy_actor_type=strategy_actor,
                signal_aggregator_actor_type=signal_aggregator_actor,
                strategy_id=spec.strategy_id,
                signal_aggregation_policy=spec.signal_aggregation_policy,
                signal_priority=spec.signal_priority,
                signal_weight=spec.signal_weight,
                conflict_group=spec.conflict_group,
            )
            bindings.append(
                StrategyRuntimeBinding(
                    strategy_id=spec.strategy_id,
                    account_id=spec.account_id,
                    strategy=strategy,
                    subscriptions=tuple(spec.subscriptions),
                    enabled=spec.enabled,
                    signal_aggregation_policy=SignalAggregationPolicy(
                        spec.signal_aggregation_policy
                    ),
                    signal_priority=spec.signal_priority,
                    signal_weight=spec.signal_weight,
                    conflict_group=spec.conflict_group,
                    pipeline=pipeline,
                )
            )
        return tuple(bindings)

    @staticmethod
    def normalize_strategy_specs(
        strategy_specs: Sequence[StrategyRuntimeSpec] | None,
        *,
        strategies: tuple[Strategy, ...],
        strategy_id: StrategyId | None,
        account_id: AccountId,
        signal_aggregation_policy: str,
        signal_priority: int,
        signal_weight: Decimal,
        conflict_group: str,
    ) -> tuple[StrategyRuntimeSpec, ...]:
        """Return validated specs matching the injected strategy instances."""
        if strategy_specs is not None:
            return tuple(strategy_specs)
        if strategy_id is None:
            raise ValueError("strategy_id is required")
        return (
            StrategyRuntimeSpec(
                strategy_id=strategy_id,
                strategy_class=strategies[0].__class__.__qualname__,
                account_id=account_id,
                subscriptions=(),
                signal_aggregation_policy=signal_aggregation_policy,
                signal_priority=signal_priority,
                signal_weight=Decimal(signal_weight),
                conflict_group=conflict_group,
            ),
        )

    @staticmethod
    def _strategy_subscription_target_timeframe(
        strategy_pipelines: Sequence[StrategyExecutionPipeline],
        *,
        fallback: str | None,
    ) -> str | None:
        """Resolve the single strategy-facing timeframe supported by this loop."""
        timeframes = tuple(
            dict.fromkeys(
                subscription.timeframe.strip()
                for strategy_pipeline in strategy_pipelines
                for subscription in strategy_pipeline.subscriptions
            )
        )
        if not timeframes:
            return fallback
        if len(timeframes) > 1:
            raise RuntimeError(
                "backtest actor loop requires one strategy subscription timeframe; got "
                + ", ".join(timeframes)
            )
        return timeframes[0]


__all__ = ["BacktestActorLoopAssembler"]
