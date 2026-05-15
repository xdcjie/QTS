"""Shared strategy execution pipeline."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import AccountId, CorrelationId, InstrumentId, StrategyId
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalAggregatorActor,
    StrategySignalEvent,
)
from qts.runtime.actors.strategy_actor import (
    StrategyActor,
    StrategyBarEvent,
    StrategyBarResult,
    StrategyFinalize,
    StrategyFinalized,
)
from qts.runtime.mailbox import Mailbox
from qts.runtime.signal_policy import SignalAggregationPolicy
from qts.strategy_sdk import PortfolioView, Strategy, StrategyContext, TargetIntent
from qts.strategy_sdk.data_view import DataView

PortfolioViewBuilder = Callable[..., PortfolioView]


@dataclass(frozen=True, slots=True)
class StrategyExecutionResult:
    """Strategy intents emitted for one strategy-facing bar."""

    bar: Bar
    intents: tuple[TargetIntent, ...]
    raw_intents: tuple[TargetIntent, ...] = ()
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    rejected_strategy_ids: tuple[StrategyId, ...] = ()
    signal_batches: tuple[AggregatedSignalBatch, ...] = ()
    conflict_group: str = "default"
    conflict_reason: str = ""
    aggregation_policy: SignalAggregationPolicy = SignalAggregationPolicy.SUM_TARGETS
    aggregation_decision_id: str | None = None
    target_before_risk: Decimal | None = None
    target_after_aggregation: Decimal | None = None


class StrategyExecutionPipeline:
    """Run strategy actors and signal aggregation for strategy-facing bars."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        strategy_id: StrategyId | None = None,
        instrument_registry: InstrumentRegistry | None,
        future_chain_registry: FutureRollRegistry | None,
        portfolio_view: PortfolioViewBuilder,
        prune_history: bool,
        strategy_actor_type: type = StrategyActor,
        signal_aggregator_actor_type: type = SignalAggregatorActor,
        signal_aggregation_policy: SignalAggregationPolicy | str = (
            SignalAggregationPolicy.SUM_TARGETS
        ),
        signal_priority: int = 0,
        signal_weight: Decimal = Decimal("1"),
        conflict_group: str = "default",
    ) -> None:
        """Create a mode-agnostic strategy execution pipeline."""
        self._strategy_id = strategy_id
        self._portfolio_view = portfolio_view
        self._strategy_bars_by_instrument: dict[InstrumentId, list[Bar]] = defaultdict(list)
        self._ctx = StrategyContext(
            instrument_registry=instrument_registry,
            future_chain_registry=future_chain_registry,
        )
        self._strategy_result_mailbox = Mailbox()
        self._strategy_ref = ActorRef(
            actor=strategy_actor_type(
                strategy=strategy,
                context=self._ctx,
                result_ref=ActorRef(mailbox=self._strategy_result_mailbox),
            ),
            mailbox=Mailbox(),
        )
        self._signal_result_mailbox = Mailbox()
        self._signal_ref = ActorRef(
            actor=signal_aggregator_actor_type(
                result_ref=ActorRef(mailbox=self._signal_result_mailbox)
            ),
            mailbox=Mailbox(),
        )
        self._signal_aggregation_policy = SignalAggregationPolicy(signal_aggregation_policy)
        self._signal_priority = signal_priority
        self._signal_weight = Decimal(signal_weight)
        self._conflict_group = conflict_group
        self._history_limit = self._history_limit_from_subscriptions() if prune_history else None

    def execute_bar(
        self,
        bar: Bar,
        *,
        account_snapshot: AccountSnapshot | object,
        latest_prices: Mapping[InstrumentId, Decimal],
        aggregate_signals: bool,
        account_id: AccountId | None = None,
        correlation_id: CorrelationId | None = None,
    ) -> StrategyExecutionResult:
        """Execute strategy logic for one completed strategy-facing bar."""
        history = self._strategy_bars_by_instrument[bar.instrument_id]
        history.append(bar)
        if self._history_limit is not None and len(history) > self._history_limit:
            del history[: len(history) - self._history_limit]
        self._strategy_ref.tell(
            StrategyBarEvent(
                bar=bar,
                data=DataView(
                    bars=self._strategy_bars_by_instrument,
                    as_of=bar.end_time,
                ),
                portfolio=self._portfolio_view(
                    account_snapshot,
                    latest_prices=latest_prices,
                ),
            )
        )
        self._strategy_ref.process_all()
        strategy_result = self._take_strategy_bar_result()
        if not aggregate_signals:
            return StrategyExecutionResult(
                bar=bar,
                intents=(),
                raw_intents=strategy_result.intents,
            )
        if not strategy_result.intents:
            return StrategyExecutionResult(
                bar=bar,
                intents=(),
                raw_intents=strategy_result.intents,
                signal_batches=(),
            )

        self._signal_ref.tell(
            StrategySignalEvent(
                bar=bar,
                intents=strategy_result.intents,
                account_id=account_id,
                correlation_id=correlation_id,
                strategy_id=self._strategy_id,
                signal_weight=self._signal_weight,
                signal_priority=self._signal_priority,
                conflict_group=self._conflict_group,
                signal_aggregation_policy=self._signal_aggregation_policy,
            )
        )
        self._signal_ref.process_all()
        signal_batches = self._take_signal_batches()
        aggregated_intents = tuple(intent for batch in signal_batches for intent in batch.intents)
        return StrategyExecutionResult(
            bar=bar,
            intents=aggregated_intents,
            raw_intents=strategy_result.intents,
            signal_batches=signal_batches,
            contributing_strategy_ids=tuple(
                strategy_id
                for batch in signal_batches
                for strategy_id in batch.contributing_strategy_ids
            ),
            rejected_strategy_ids=tuple(
                strategy_id
                for batch in signal_batches
                for strategy_id in batch.rejected_strategy_ids
            ),
            conflict_group=",".join(
                dict.fromkeys(
                    batch.conflict_group for batch in signal_batches if batch.conflict_group
                )
            ),
            conflict_reason="; ".join(
                batch.conflict_reason for batch in signal_batches if batch.conflict_reason
            ),
            aggregation_policy=signal_batches[0].aggregation_policy,
            aggregation_decision_id=signal_batches[0].aggregation_decision_id,
            target_before_risk=signal_batches[0].target_before_risk,
            target_after_aggregation=signal_batches[0].target_after_aggregation,
        )

    def finalize(self) -> tuple[TargetIntent, ...]:
        """Finalize the strategy and return finalization intents."""
        self._strategy_ref.tell(StrategyFinalize())
        self._strategy_ref.process_all()
        return self._take_strategy_finalized().intents

    def _history_limit_from_subscriptions(self) -> int | None:
        """Return the maximum requested subscription warmup."""
        if not self._ctx.subscriptions:
            return None
        return max(subscription.warmup for subscription in self._ctx.subscriptions)

    def _take_strategy_bar_result(self) -> StrategyBarResult:
        """Return the single strategy actor result for one bar."""
        if self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor did not emit a bar result")
        result = self._strategy_result_mailbox.get()
        if not isinstance(result, StrategyBarResult):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one bar result")
        return result

    def _take_signal_batches(self) -> tuple[AggregatedSignalBatch, ...]:
        """Return all signal aggregation batches for one strategy-facing bar."""
        batches: list[AggregatedSignalBatch] = []
        while not self._signal_result_mailbox.empty():
            result = self._signal_result_mailbox.get()
            if not isinstance(result, AggregatedSignalBatch):
                raise TypeError(f"unexpected signal aggregator result: {type(result).__name__}")
            batches.append(result)
        if not batches:
            raise RuntimeError("signal aggregator actor did not emit a batch")
        return tuple(batches)

    def _take_strategy_finalized(self) -> StrategyFinalized:
        """Return the single strategy finalization result."""
        if self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor did not emit finalization result")
        result = self._strategy_result_mailbox.get()
        if not isinstance(result, StrategyFinalized):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not self._strategy_result_mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one finalization result")
        return result


__all__ = ["StrategyExecutionPipeline", "StrategyExecutionResult"]
