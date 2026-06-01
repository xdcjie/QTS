"""Backtest strategy-signal evidence event writing."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, TypeAlias

from qts.backtest.dependencies import (
    MarketDataProvenanceProvider,
)
from qts.core.ids import AccountId, CorrelationId, StrategyId
from qts.domain.market_data import Bar
from qts.reporting.backtest import (
    broker_capability_payload,
)
from qts.runtime.broker_runtime_topology import StrategyRuntimeBinding
from qts.runtime.sinks.base import RuntimeEvent
from qts.runtime.strategy_execution_pipeline import (
    StrategyExecutionResult,
)

if TYPE_CHECKING:
    from qts.execution.execution_adapter import ExecutionEvidenceProvider

BacktestActorLoopState: TypeAlias = SimpleNamespace
BacktestStrategyExecution: TypeAlias = tuple[StrategyRuntimeBinding, StrategyExecutionResult]
BacktestStrategyBarExecution: TypeAlias = tuple[BacktestStrategyExecution, ...]


class BacktestSignalEventWriter:
    """Write backtest strategy-signal, conflict, market-data, and broker-reject events."""

    def __init__(
        self,
        *,
        account_id: AccountId,
        execution_adapter: ExecutionEvidenceProvider,
        market_data_provenance_for: MarketDataProvenanceProvider,
    ) -> None:
        """Bind the writer to the backtest run's account, adapter, and provenance source."""
        self._account_id = account_id
        self._execution_adapter = execution_adapter
        self._market_data_provenance_for = market_data_provenance_for

    def write_market_data_event(
        self,
        state: BacktestActorLoopState,
        bar: Bar,
        correlation_id: CorrelationId,
    ) -> None:
        """Update latest price state and emit the normalized market-data event."""
        state.latest_prices[bar.instrument_id] = bar.close
        market_data_payload: dict[str, object] = {
            "instrument_id": bar.instrument_id.value,
            "timeframe": bar.timeframe,
            "end_time": bar.end_time.isoformat(),
        }
        market_data_payload.update(self._market_data_provenance_for(bar))
        state.sink.write(
            RuntimeEvent(
                kind="runtime.market_data",
                payload=market_data_payload,
                correlation_id=correlation_id,
                instrument_id=bar.instrument_id,
            )
        )

    def write_strategy_signal_events(
        self,
        state: BacktestActorLoopState,
        strategy_result: BacktestStrategyBarExecution,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit raw strategy signal and intent events."""
        for execution in strategy_result:
            self.write_strategy_binding_signal_events(
                state,
                execution,
                correlation_id,
            )

    def write_strategy_binding_signal_events(
        self,
        state: BacktestActorLoopState,
        execution: BacktestStrategyExecution,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit raw strategy signal and intent events for one binding."""
        binding, result = execution
        for intent in result.raw_intents:
            signal_payload = {
                "instrument_id": intent.asset.instrument_id.value,
                "intent_type": intent.intent_type.value,
                "value": str(intent.value) if intent.value is not None else None,
                "aggregation_policy": binding.signal_aggregation_policy.value,
                "signal_weight": str(binding.signal_weight),
                "signal_priority": binding.signal_priority,
                "conflict_group": binding.conflict_group,
                "order_spec": intent.order_spec.to_payload(),
            }
            intent_payload = {
                "instrument_id": intent.asset.instrument_id.value,
                "intent_type": intent.intent_type.value,
                "value": str(intent.value) if intent.value is not None else None,
                "order_spec": intent.order_spec.to_payload(),
            }
            if intent.metadata:
                signal_payload["metadata"] = dict(intent.metadata)
                intent_payload["metadata"] = dict(intent.metadata)
            state.sink.write(
                RuntimeEvent(
                    kind="runtime.signal_received",
                    payload=signal_payload,
                    correlation_id=correlation_id,
                    instrument_id=intent.asset.instrument_id,
                    account_id=binding.account_id,
                    strategy_id=binding.strategy_id,
                )
            )
            state.sink.write(
                RuntimeEvent(
                    kind="runtime.strategy_intent",
                    payload=intent_payload,
                    correlation_id=correlation_id,
                    instrument_id=intent.asset.instrument_id,
                    account_id=binding.account_id,
                    strategy_id=binding.strategy_id,
                )
            )

    def write_signal_batch_events(
        self,
        state: BacktestActorLoopState,
        batch: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit aggregation, conflict, and rejection events for a signal batch."""
        state.sink.write(
            RuntimeEvent(
                kind="runtime.signal_aggregated",
                payload={
                    "aggregation_decision_id": batch.aggregation_decision_id,
                    "aggregation_policy": batch.aggregation_policy.value,
                    "contributing_strategy_ids": [
                        strategy_id.value for strategy_id in batch.contributing_strategy_ids
                    ],
                    "conflict_group": batch.conflict_group,
                    "intent_count": len(batch.intents),
                    "target_before_risk": (
                        str(batch.target_before_risk)
                        if batch.target_before_risk is not None
                        else None
                    ),
                    "target_after_aggregation": (
                        str(batch.target_after_aggregation)
                        if batch.target_after_aggregation is not None
                        else None
                    ),
                },
                correlation_id=correlation_id,
                instrument_id=batch.instrument_id,
                account_id=batch.account_id if batch.account_id is not None else self._account_id,
                strategy_id=(
                    batch.contributing_strategy_ids[0]
                    if len(batch.contributing_strategy_ids) == 1
                    else None
                ),
            )
        )
        if batch.conflict_reason:
            self.write_batch_conflict_events(state, batch, correlation_id)

    def write_batch_conflict_events(
        self,
        state: BacktestActorLoopState,
        batch: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit conflict and rejection evidence for a rejected signal batch."""
        state.sink.write(
            RuntimeEvent(
                kind="runtime.signal_conflict_detected",
                payload={
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
                instrument_id=batch.instrument_id,
                account_id=batch.account_id if batch.account_id is not None else self._account_id,
                strategy_id=None,
            )
        )
        state.sink.write(
            RuntimeEvent(
                kind="runtime.signal_rejected",
                payload={
                    "conflict_reason": batch.conflict_reason,
                    "aggregation_decision_id": batch.aggregation_decision_id,
                    "rejected_strategy_ids": [
                        strategy_id.value for strategy_id in batch.rejected_strategy_ids
                    ],
                    "conflict_group": batch.conflict_group,
                    "aggregation_policy": batch.aggregation_policy.value,
                    "target_before_risk": (
                        str(batch.target_before_risk)
                        if batch.target_before_risk is not None
                        else None
                    ),
                    "target_after_aggregation": (
                        str(batch.target_after_aggregation)
                        if batch.target_after_aggregation is not None
                        else None
                    ),
                },
                correlation_id=correlation_id,
                instrument_id=batch.instrument_id,
                account_id=batch.account_id if batch.account_id is not None else self._account_id,
                strategy_id=None,
            )
        )

    def write_broker_reject_event(
        self,
        state: BacktestActorLoopState,
        intent: Any,
        correlation_id: CorrelationId,
        exc: ValueError,
        strategy_id: StrategyId,
        account_id: AccountId,
    ) -> None:
        """Emit a normalized broker capability rejection event."""
        state.sink.write(
            RuntimeEvent(
                kind="runtime.broker_rejected",
                payload={
                    "reason_code": "unsupported_order_type",
                    "reason": str(exc),
                    "broker_capability_model": broker_capability_payload(self._execution_adapter),
                },
                correlation_id=correlation_id,
                instrument_id=intent.asset.instrument_id,
                account_id=account_id,
                strategy_id=strategy_id,
            )
        )


__all__ = ["BacktestSignalEventWriter"]
