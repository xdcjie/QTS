"""Narrow runtime context consumed by market-data coordination."""

from __future__ import annotations

from collections.abc import MutableMapping
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol, TypeAlias

from qts.core.ids import AccountId, CausationId, CorrelationId, InstrumentId, StrategyId
from qts.data.permissions import MarketDataPermissionEvent
from qts.data.sources.streaming_market_data_source import (
    StreamingMarketDataDegradation,
    StreamingMarketDataSubscriptionEvent,
)
from qts.domain.market_data import Bar
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalContribution,
)
from qts.runtime.broker_runtime_topology import (
    AccountRuntimePartition,
    StrategyRuntimeBinding,
)
from qts.runtime.intent_processing import ProcessedIntent
from qts.runtime.market_data_flow import MarketDataFlowResult
from qts.runtime.order_result import RuntimeOrderResult
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.state import RuntimeSessionState
from qts.strategy_sdk import TargetIntent

if TYPE_CHECKING:
    from qts.runtime.session import RuntimeSession


MarketDataSourceEvent: TypeAlias = (
    Bar
    | StreamingMarketDataDegradation
    | StreamingMarketDataSubscriptionEvent
    | MarketDataPermissionEvent
)


class RuntimeMarketDataCoordinatorContext(Protocol):
    """Session operations required by runtime market-data coordination."""

    @property
    def strategy_subscriptions(self) -> tuple[InstrumentId, ...]: ...

    def replace_strategy_subscriptions(
        self,
        subscriptions: tuple[InstrumentId, ...],
    ) -> None: ...

    def publish_source_event(self, event: MarketDataSourceEvent) -> MarketDataFlowResult: ...

    def write(self, event: RuntimeEvent) -> None: ...

    @property
    def state(self) -> RuntimeSessionState: ...

    def degrade(self) -> RuntimeSessionState: ...

    def account_snapshots(self) -> tuple[tuple[AccountId | None, AccountSnapshot], ...]: ...

    @property
    def topology_configured(self) -> bool: ...

    def blocked_reason(self) -> str | None: ...

    def permission_block_result(self, reason_code: str) -> RuntimeOrderResult: ...

    def write_order_permission_blocked(
        self,
        reason_code: str,
        order_result: RuntimeOrderResult,
        *,
        correlation_id: CorrelationId,
        instrument_id: InstrumentId,
    ) -> None: ...

    @property
    def warmup_bars(self) -> int: ...

    @property
    def order_submission_enabled(self) -> bool: ...

    @property
    def latest_prices(self) -> MutableMapping[InstrumentId, Decimal]: ...

    @property
    def strategy_bindings(self) -> tuple[StrategyRuntimeBinding, ...]: ...

    def resolve_partition(self, account_id: AccountId | None) -> AccountRuntimePartition: ...

    def aggregate_signal_batches(
        self,
        bar: Bar,
        contributions: tuple[SignalContribution, ...],
        *,
        account_id: AccountId | None = None,
        correlation_id: CorrelationId | None = None,
    ) -> tuple[AggregatedSignalBatch, ...]: ...

    @property
    def event_index(self) -> int: ...

    def advance_event_index(self) -> None: ...

    @property
    def fallback_strategy_id(self) -> StrategyId | None: ...

    def process_intent(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        account_id: AccountId | None,
        strategy_id: StrategyId,
        correlation_id: CorrelationId,
        partition: AccountRuntimePartition,
        contributing_strategy_ids: tuple[StrategyId, ...] = (),
        aggregation_decision_id: str | None = None,
        conflict_reason: str | None = None,
    ) -> ProcessedIntent: ...

    def write_event(
        self,
        kind: str,
        payload: dict[str, object],
        *,
        correlation_id: CorrelationId | None = None,
        instrument_id: InstrumentId | None = None,
        account_id: AccountId | None = None,
        strategy_id: StrategyId | None = None,
        causation_id: CausationId | None = None,
    ) -> None: ...

    def record_account_snapshots(self) -> tuple[str, ...]: ...


class RuntimeMarketDataSessionContext:
    """Typed facade over the RuntimeSession state used by market-data coordination."""

    def __init__(self, runtime_session: RuntimeSession) -> None:
        self._runtime_session = runtime_session

    @property
    def strategy_subscriptions(self) -> tuple[InstrumentId, ...]:
        return self._runtime_session._strategy_subscriptions

    def replace_strategy_subscriptions(
        self,
        subscriptions: tuple[InstrumentId, ...],
    ) -> None:
        self._runtime_session._strategy_subscriptions = subscriptions

    def publish_source_event(self, event: MarketDataSourceEvent) -> MarketDataFlowResult:
        return self._runtime_session._market_data_flow.publish_source_event(event)

    def write(self, event: RuntimeEvent) -> None:
        self._runtime_session._write(event)

    @property
    def state(self) -> RuntimeSessionState:
        return self._runtime_session.state

    def degrade(self) -> RuntimeSessionState:
        return self._runtime_session.degrade()

    def account_snapshots(self) -> tuple[tuple[AccountId | None, AccountSnapshot], ...]:
        return tuple(
            (account_id, partition.account_actor.snapshot())
            for account_id, partition in self._runtime_session._account_partitions.items()
        )

    @property
    def topology_configured(self) -> bool:
        return self._runtime_session._topology is not None

    def blocked_reason(self) -> str | None:
        return self._runtime_session._blocked_reason()

    def permission_block_result(self, reason_code: str) -> RuntimeOrderResult:
        return self._runtime_session._permission_block_result(reason_code)

    def write_order_permission_blocked(
        self,
        reason_code: str,
        order_result: RuntimeOrderResult,
        *,
        correlation_id: CorrelationId,
        instrument_id: InstrumentId,
    ) -> None:
        self._runtime_session._write_order_permission_blocked(
            reason_code,
            order_result,
            correlation_id=correlation_id,
            instrument_id=instrument_id,
        )

    @property
    def warmup_bars(self) -> int:
        return self._runtime_session._dependencies.warmup_bars

    @property
    def order_submission_enabled(self) -> bool:
        return self._runtime_session._dependencies.order_submission_enabled

    @property
    def latest_prices(self) -> MutableMapping[InstrumentId, Decimal]:
        return self._runtime_session._latest_prices

    @property
    def strategy_bindings(self) -> tuple[StrategyRuntimeBinding, ...]:
        return self._runtime_session._strategy_bindings

    def resolve_partition(self, account_id: AccountId | None) -> AccountRuntimePartition:
        return self._runtime_session._resolve_partition(account_id)

    def aggregate_signal_batches(
        self,
        bar: Bar,
        contributions: tuple[SignalContribution, ...],
        *,
        account_id: AccountId | None = None,
        correlation_id: CorrelationId | None = None,
    ) -> tuple[AggregatedSignalBatch, ...]:
        return self._runtime_session._aggregate_signal_batches(
            bar,
            contributions,
            account_id=account_id,
            correlation_id=correlation_id,
        )

    @property
    def event_index(self) -> int:
        return self._runtime_session._event_index

    def advance_event_index(self) -> None:
        self._runtime_session._event_index += 1

    @property
    def fallback_strategy_id(self) -> StrategyId | None:
        return self._runtime_session._resolved_strategy_id

    def process_intent(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        account_id: AccountId | None,
        strategy_id: StrategyId,
        correlation_id: CorrelationId,
        partition: AccountRuntimePartition,
        contributing_strategy_ids: tuple[StrategyId, ...] = (),
        aggregation_decision_id: str | None = None,
        conflict_reason: str | None = None,
    ) -> ProcessedIntent:
        return self._runtime_session._process_intent(
            intent,
            bar=bar,
            account_id=account_id,
            strategy_id=strategy_id,
            correlation_id=correlation_id,
            partition=partition,
            contributing_strategy_ids=contributing_strategy_ids,
            aggregation_decision_id=aggregation_decision_id,
            conflict_reason=conflict_reason,
        )

    def write_event(
        self,
        kind: str,
        payload: dict[str, object],
        *,
        correlation_id: CorrelationId | None = None,
        instrument_id: InstrumentId | None = None,
        account_id: AccountId | None = None,
        strategy_id: StrategyId | None = None,
        causation_id: CausationId | None = None,
    ) -> None:
        self._runtime_session._write_event(
            kind,
            payload,
            correlation_id=correlation_id,
            instrument_id=instrument_id,
            account_id=account_id,
            strategy_id=strategy_id,
            causation_id=causation_id,
        )

    def record_account_snapshots(self) -> tuple[str, ...]:
        return self._runtime_session._record_account_snapshots()


__all__ = [
    "MarketDataSourceEvent",
    "RuntimeMarketDataCoordinatorContext",
    "RuntimeMarketDataSessionContext",
]
