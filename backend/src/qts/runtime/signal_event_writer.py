"""Runtime strategy-signal evidence event writing."""

from __future__ import annotations

from typing import Any

from qts.core.ids import CorrelationId
from qts.domain.market_data import Bar
from qts.runtime.market_data_context import RuntimeMarketDataCoordinatorContext


class RuntimeSignalEventWriter:
    """Write strategy-signal, conflict, and aggregation evidence events."""

    def __init__(self, context: RuntimeMarketDataCoordinatorContext) -> None:
        """Bind the writer to the runtime market-data coordinator context."""
        self._context = context

    def write_strategy_intent_events(
        self,
        binding: Any,
        strategy_result: Any,
        correlation_id: CorrelationId,
    ) -> None:
        """Emit raw strategy signal and intent events."""
        context = self._context
        for intent in strategy_result.raw_intents:
            signal_payload = {
                "instrument_id": intent.asset.instrument_id.value,
                "intent_type": intent.intent_type.value,
                "value": str(intent.value) if intent.value is not None else None,
                "aggregation_policy": binding.signal_aggregation_policy.value,
                "signal_weight": str(binding.signal_weight),
                "signal_priority": binding.signal_priority,
                "conflict_group": binding.conflict_group,
            }
            intent_payload = {
                "instrument_id": intent.asset.instrument_id.value,
                "intent_type": intent.intent_type.value,
                "value": str(intent.value) if intent.value is not None else None,
            }
            if intent.metadata:
                signal_payload["metadata"] = dict(intent.metadata)
                intent_payload["metadata"] = dict(intent.metadata)
            context.write_event(
                "runtime.signal_received",
                signal_payload,
                correlation_id=correlation_id,
                instrument_id=intent.asset.instrument_id,
                strategy_id=binding.strategy_id,
                account_id=binding.account_id,
            )
            context.write_event(
                "runtime.strategy_intent",
                intent_payload,
                correlation_id=correlation_id,
                instrument_id=intent.asset.instrument_id,
                strategy_id=binding.strategy_id,
                account_id=binding.account_id,
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


__all__ = ["RuntimeSignalEventWriter"]
