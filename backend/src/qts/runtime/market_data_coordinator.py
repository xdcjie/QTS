"""Runtime market-data coordination for paper/live sessions."""

from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, TypeAlias, cast

from qts.core.ids import AccountId, CorrelationId, InstrumentId
from qts.data.permissions import MarketDataPermissionEvent
from qts.data.sources.streaming_market_data_source import (
    StreamingMarketDataDegradation,
    StreamingMarketDataSubscriptionEvent,
)
from qts.data.subscriptions import UniverseSubscriptionDelta, UniverseSubscriptionPlanner
from qts.domain.market_data import Bar
from qts.runtime.actors.account_actor import (
    AccountSnapshot,
    DrainPositionClosedEvents,
    GetAccountSnapshot,
)
from qts.runtime.actors.signal_aggregator_actor import SignalContribution
from qts.runtime.market_data_context import (
    RuntimeMarketDataCoordinatorContext,
    RuntimeMarketDataSessionContext,
)
from qts.runtime.runtime_event_writer import RuntimeEventWriter
from qts.runtime.session import RuntimeSessionResult
from qts.runtime.state import RuntimeSessionState

if TYPE_CHECKING:
    from qts.runtime.session import RuntimeSession

MarketDataDispatchState: TypeAlias = SimpleNamespace


class RuntimeMarketDataCoordinator:
    """Own market-data source events and strategy/order actor coordination."""

    def __init__(self, context: object) -> None:
        self._context = self._coerce_context(context)
        self._runtime_event_writer = RuntimeEventWriter(write=self._context.write)

    @classmethod
    def _coerce_context(cls, context: object) -> RuntimeMarketDataCoordinatorContext:
        if cls._looks_like_context(context):
            return cast(RuntimeMarketDataCoordinatorContext, context)
        return RuntimeMarketDataSessionContext(cast("RuntimeSession", context))

    @staticmethod
    def _looks_like_context(context: object) -> bool:
        return all(
            hasattr(context, attribute)
            for attribute in ("strategy_subscriptions", "replace_strategy_subscriptions", "write")
        )

    def materialize_universe_subscription_delta(
        self,
        target: Iterable[InstrumentId],
    ) -> UniverseSubscriptionDelta:
        """Apply a strategy universe update to runtime subscription membership."""
        context = self._context
        target_subscriptions = tuple(sorted(set(target), key=lambda item: item.value))
        delta = UniverseSubscriptionPlanner().plan(
            current=context.strategy_subscriptions,
            target=target_subscriptions,
        )
        context.replace_strategy_subscriptions(target_subscriptions)
        return delta

    def on_market_data_source_event(
        self,
        event: Bar
        | StreamingMarketDataDegradation
        | StreamingMarketDataSubscriptionEvent
        | MarketDataPermissionEvent,
    ) -> RuntimeSessionResult:
        """Handle a source market-data event, including degradation and permission signals."""
        context = self._context
        if isinstance(event, Bar):
            return self.on_market_data(event)
        flow_result = context.publish_source_event(event)
        reason_code: str | None = None
        for runtime_event in flow_result.runtime_events:
            context.write(runtime_event)
            if runtime_event.kind == "runtime.degraded":
                if context.state is not RuntimeSessionState.DEGRADED:
                    context.degrade()
                reason_code = "RUNTIME_DEGRADED"
        account_snapshots = context.account_snapshots()
        return RuntimeSessionResult(
            market_data=(),
            orders=(),
            fills=(),
            account_snapshot=self._single_account_snapshot(account_snapshots),
            account_snapshots=account_snapshots,
            reason_code=reason_code,
        )

    def on_market_data(self, source_bar: Bar) -> RuntimeSessionResult:
        """Handle one source bar through named runtime dispatch stages."""
        routed = self.route_source_bar(source_bar)
        if routed is not None:
            return routed

        bars = self.derive_market_data(source_bar)
        dispatch = MarketDataDispatchState(
            orders=[],
            fills=[],
            order_results=[],
            reason_code=None,
        )
        for bar in bars:
            self.trigger_strategy_for_bar(bar, dispatch)
        return self.finish_market_data_dispatch(bars, dispatch)

    def route_source_bar(self, source_bar: Bar) -> RuntimeSessionResult | None:
        """Reject source bars that do not match topology subscriptions."""
        context = self._context
        if (
            context.topology_configured
            and source_bar.instrument_id not in context.strategy_subscriptions
        ):
            snapshots = context.account_snapshots()
            return RuntimeSessionResult(
                market_data=(),
                orders=(),
                fills=(),
                account_snapshot=self._single_account_snapshot(snapshots),
                account_snapshots=snapshots,
                reason_code="INSTRUMENT_NOT_SUBSCRIBED",
            )
        return None

    def derive_market_data(self, source_bar: Bar) -> tuple[Bar, ...]:
        """Publish a source bar and return strategy-facing bars."""
        context = self._context
        flow_result = context.publish_source_event(source_bar)
        for event in flow_result.runtime_events:
            context.write(event)
            if (
                event.kind == "runtime.degraded"
                and context.state is not RuntimeSessionState.DEGRADED
            ):
                context.degrade()

        return flow_result.market_data

    def trigger_strategy_for_bar(self, bar: Bar, dispatch: MarketDataDispatchState) -> None:
        """Trigger strategy/risk/order processing for one strategy-facing bar."""
        context = self._context
        correlation_id = self.market_data_correlation_id(bar)
        self.record_market_data_bar(bar, correlation_id)

        blocked_reason = context.blocked_reason()
        if blocked_reason is not None:
            dispatch.reason_code = blocked_reason
            order_result = context.permission_block_result(blocked_reason)
            dispatch.order_results.append(order_result)
            context.write_order_permission_blocked(
                blocked_reason,
                order_result,
                correlation_id=correlation_id,
                instrument_id=bar.instrument_id,
            )
            return

        bindings_for_bar = self.bind_strategy_pipelines(bar)
        if context.topology_configured and not bindings_for_bar:
            dispatch.reason_code = "INSTRUMENT_NOT_SUBSCRIBED"
            return

        aggregate_signals = context.event_index >= context.warmup_bars
        contributions_by_account = self.execute_strategy_bindings(
            bar,
            bindings_for_bar,
            aggregate_signals=aggregate_signals,
            correlation_id=correlation_id,
        )
        if aggregate_signals:
            self.process_aggregated_signal_contributions(
                bar,
                contributions_by_account,
                correlation_id=correlation_id,
                dispatch=dispatch,
            )
        context.advance_event_index()

    def finish_market_data_dispatch(
        self,
        bars: tuple[Bar, ...],
        dispatch: MarketDataDispatchState,
    ) -> RuntimeSessionResult:
        """Build the runtime result and emit account snapshots for processed bars."""
        account_snapshots = self._context.account_snapshots()
        if bars:
            self._write_account_snapshots()
        return RuntimeSessionResult(
            market_data=bars,
            orders=tuple(dispatch.orders),
            fills=tuple(dispatch.fills),
            account_snapshot=self._single_account_snapshot(account_snapshots),
            account_snapshots=account_snapshots,
            reason_code=dispatch.reason_code,
            order_results=tuple(dispatch.order_results),
        )

    def market_data_correlation_id(self, bar: Bar) -> CorrelationId:
        """Create the stable correlation id for one strategy-facing bar."""
        return CorrelationId(
            f"md:{bar.instrument_id.value}:{bar.timeframe}:{bar.end_time.isoformat()}"
        )

    def record_market_data_bar(self, bar: Bar, correlation_id: CorrelationId) -> None:
        """Record latest price state and the normalized market-data runtime event."""
        context = self._context
        context.latest_prices[bar.instrument_id] = bar.close
        context.write_event(
            "runtime.market_data",
            {
                "instrument_id": bar.instrument_id.value,
                "timeframe": bar.timeframe,
                "end_time": bar.end_time.isoformat(),
            },
            correlation_id=correlation_id,
            instrument_id=bar.instrument_id,
        )

    def bind_strategy_pipelines(self, bar: Bar) -> list[Any]:
        """Return enabled strategy bindings that should see this bar."""
        return [
            binding
            for binding in self._context.strategy_bindings
            if binding.enabled
            and (not binding.subscriptions or bar.instrument_id in binding.subscriptions)
        ]

    def execute_strategy_bindings(
        self,
        bar: Bar,
        bindings_for_bar: list[Any],
        *,
        aggregate_signals: bool,
        correlation_id: CorrelationId,
    ) -> dict[AccountId | None, list[SignalContribution]]:
        """Execute strategy pipelines and collect contributions for aggregation."""
        context = self._context
        contributions_by_account: dict[AccountId | None, list[SignalContribution]] = {}
        for binding in bindings_for_bar:
            strategy_result = binding.pipeline.execute_bar(
                bar,
                account_snapshot=context.resolve_partition(binding.account_id).account_ref.ask(
                    GetAccountSnapshot()
                ),
                latest_prices=context.latest_prices,
                aggregate_signals=aggregate_signals,
                account_id=binding.account_id,
                correlation_id=correlation_id,
            )
            self.write_strategy_intent_events(binding, strategy_result, correlation_id)
            if aggregate_signals:
                self.collect_signal_contributions(
                    binding,
                    strategy_result.raw_intents,
                    contributions_by_account,
                )
        return contributions_by_account

    def write_strategy_intent_events(
        self,
        binding: Any,
        strategy_result: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit raw strategy signal and intent events."""
        context = self._context
        for intent in strategy_result.raw_intents:
            context.write_event(
                "runtime.signal_received",
                {
                    "instrument_id": intent.asset.instrument_id.value,
                    "intent_type": intent.intent_type.value,
                    "value": str(intent.value) if intent.value is not None else None,
                    "aggregation_policy": binding.signal_aggregation_policy.value,
                    "signal_weight": str(binding.signal_weight),
                    "signal_priority": binding.signal_priority,
                    "conflict_group": binding.conflict_group,
                },
                correlation_id=correlation_id,
                instrument_id=intent.asset.instrument_id,
                strategy_id=binding.strategy_id,
                account_id=binding.account_id,
            )
            context.write_event(
                "runtime.strategy_intent",
                {
                    "instrument_id": intent.asset.instrument_id.value,
                    "intent_type": intent.intent_type.value,
                    "value": str(intent.value) if intent.value is not None else None,
                },
                correlation_id=correlation_id,
                instrument_id=intent.asset.instrument_id,
                strategy_id=binding.strategy_id,
                account_id=binding.account_id,
            )

    def collect_signal_contributions(
        self,
        binding: Any,
        raw_intents: Iterable[Any],
        contributions_by_account: dict[AccountId | None, list[SignalContribution]],
    ) -> None:
        """Group strategy contributions by account for signal aggregation."""
        for intent in raw_intents:
            contributions_by_account.setdefault(binding.account_id, []).append(
                SignalContribution(
                    strategy_id=binding.strategy_id,
                    intent=intent,
                    aggregation_policy=binding.signal_aggregation_policy,
                    priority=binding.signal_priority,
                    weight=binding.signal_weight,
                    conflict_group=binding.conflict_group,
                )
            )

    def process_aggregated_signal_contributions(
        self,
        bar: Bar,
        contributions_by_account: dict[AccountId | None, list[SignalContribution]],
        *,
        correlation_id: CorrelationId,
        dispatch: MarketDataDispatchState,
    ) -> None:
        """Aggregate collected signals and submit resulting intents."""
        context = self._context
        for account_id, contributions in contributions_by_account.items():
            partition = context.resolve_partition(account_id)
            aggregated_batches = context.aggregate_signal_batches(
                bar,
                tuple(contributions),
                account_id=account_id,
                correlation_id=correlation_id,
            )
            for batch in aggregated_batches:
                self.process_signal_batch(
                    bar,
                    batch,
                    account_id=account_id,
                    partition=partition,
                    correlation_id=correlation_id,
                    dispatch=dispatch,
                )

    def process_signal_batch(
        self,
        bar: Bar,
        batch: Any,
        *,
        account_id: AccountId | None,
        partition: Any,
        correlation_id: CorrelationId,
        dispatch: MarketDataDispatchState,
    ) -> None:
        """Emit aggregation events and process accepted batch intents."""
        if batch.conflict_reason:
            self.write_signal_conflict_events(
                bar,
                batch,
                partition=partition,
                correlation_id=correlation_id,
            )
        self.write_signal_aggregated_event(
            bar,
            batch,
            partition=partition,
            correlation_id=correlation_id,
        )
        if not batch.intents:
            return
        if not self._context.order_submission_enabled:
            dispatch.reason_code = "ORDER_SUBMISSION_DISABLED"
            return
        for intent in batch.intents:
            self.process_batch_intent(
                bar,
                batch,
                intent,
                account_id=account_id,
                partition=partition,
                correlation_id=correlation_id,
                dispatch=dispatch,
            )

    def write_signal_conflict_events(
        self,
        bar: Bar,
        batch: Any,
        *,
        partition: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit conflict and rejection evidence for an aggregated signal batch."""
        context = self._context
        context.write_event(
            "runtime.signal_conflict_detected",
            {
                "conflict_reason": batch.conflict_reason,
                "aggregation_decision_id": batch.aggregation_decision_id,
                "rejected_strategy_ids": [
                    strategy_id.value for strategy_id in batch.rejected_strategy_ids
                ],
                "conflicts": [
                    {
                        "instrument_key": conflict.instrument_key,
                        "strategy_ids": [
                            strategy_id.value for strategy_id in conflict.strategy_ids
                        ],
                        "reason": conflict.reason,
                    }
                    for conflict in batch.conflicts
                ],
                "conflict_group": batch.conflict_group,
                "aggregation_policy": batch.aggregation_policy.value,
            },
            correlation_id=correlation_id,
            account_id=partition.account_id,
            instrument_id=bar.instrument_id,
        )
        context.write_event(
            "runtime.signal_rejected",
            {
                "conflict_reason": batch.conflict_reason,
                "aggregation_decision_id": batch.aggregation_decision_id,
                "rejected_strategy_ids": [
                    strategy_id.value for strategy_id in batch.rejected_strategy_ids
                ],
                "conflict_group": batch.conflict_group,
                "aggregation_policy": batch.aggregation_policy.value,
                "target_before_risk": (
                    str(batch.target_before_risk) if batch.target_before_risk is not None else None
                ),
                "target_after_aggregation": (
                    str(batch.target_after_aggregation)
                    if batch.target_after_aggregation is not None
                    else None
                ),
            },
            correlation_id=correlation_id,
            account_id=partition.account_id,
            instrument_id=bar.instrument_id,
        )

    def write_signal_aggregated_event(
        self,
        bar: Bar,
        batch: Any,
        *,
        partition: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit the accepted aggregate signal event for a batch."""
        self._context.write_event(
            "runtime.signal_aggregated",
            {
                "aggregation_decision_id": batch.aggregation_decision_id,
                "aggregation_policy": batch.aggregation_policy.value,
                "contributing_strategy_ids": [
                    strategy_id.value for strategy_id in batch.contributing_strategy_ids
                ],
                "conflict_group": batch.conflict_group,
                "intent_count": len(batch.intents),
                "target_before_risk": (
                    str(batch.target_before_risk) if batch.target_before_risk is not None else None
                ),
                "target_after_aggregation": (
                    str(batch.target_after_aggregation)
                    if batch.target_after_aggregation is not None
                    else None
                ),
            },
            correlation_id=correlation_id,
            account_id=partition.account_id,
            instrument_id=bar.instrument_id,
        )

    def process_batch_intent(
        self,
        bar: Bar,
        batch: Any,
        intent: Any,
        *,
        account_id: AccountId | None,
        partition: Any,
        correlation_id: CorrelationId,
        dispatch: MarketDataDispatchState,
    ) -> None:
        """Submit one post-aggregation intent through risk, order, and fill stages."""
        context = self._context
        strategy_id = (
            batch.contributing_strategy_ids[0]
            if batch.contributing_strategy_ids
            else context.fallback_strategy_id
        )
        if strategy_id is None:
            raise ValueError("strategy_id is required")
        processed = context.process_intent(
            intent,
            bar=bar,
            account_id=account_id,
            strategy_id=strategy_id,
            correlation_id=correlation_id,
            partition=partition,
            contributing_strategy_ids=batch.contributing_strategy_ids,
            aggregation_decision_id=batch.aggregation_decision_id,
            conflict_reason=batch.conflict_reason if batch.conflict_reason else None,
        )
        dispatch.orders.extend(processed.orders)
        dispatch.fills.extend(processed.fills)
        self._runtime_event_writer.write_risk_decision_events(
            processed.risk_decisions,
            correlation_id=correlation_id,
            account_id=partition.account_id,
            instrument_id=intent.asset.instrument_id,
            strategy_id=strategy_id,
        )
        self._runtime_event_writer.write_order_events(
            processed.orders,
            partition.order_manager_ref,
            fallback_contributing_strategy_ids=batch.contributing_strategy_ids,
        )
        self._runtime_event_writer.write_fill_events(
            processed.fills,
            partition.order_manager_ref,
        )
        closed_events = partition.account_ref.ask(DrainPositionClosedEvents())
        if closed_events:
            self._runtime_event_writer.write_position_closed_events(
                closed_events,
                account_id=partition.account_id,
                strategy_id=strategy_id,
                correlation_id=correlation_id,
            )

    @staticmethod
    def _single_account_snapshot(
        account_snapshots: tuple[tuple[AccountId | None, AccountSnapshot], ...],
    ) -> AccountSnapshot | None:
        if len(account_snapshots) != 1:
            return None
        return account_snapshots[0][1]

    def _write_account_snapshots(self) -> None:
        context = self._context
        for account_id, snapshot in context.account_snapshots():
            context.write_event(
                "runtime.account_snapshot",
                {
                    "cash": {currency: str(balance) for currency, balance in snapshot.cash.items()},
                    "positions": {
                        instrument_id.value: str(position.quantity)
                        for instrument_id, position in snapshot.positions.items()
                    },
                },
                account_id=account_id,
            )
        context.record_account_snapshots()


__all__ = ["RuntimeMarketDataCoordinator"]
