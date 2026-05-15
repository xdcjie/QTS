"""Runtime market-data coordination for paper/live sessions."""

from __future__ import annotations

from typing import Any

from qts.core.ids import AccountId, CausationId, CorrelationId, InstrumentId, StrategyId
from qts.data.permissions import MarketDataPermissionEvent
from qts.data.sources.streaming_market_data_source import (
    StreamingMarketDataDegradation,
    StreamingMarketDataSubscriptionEvent,
)
from qts.domain.market_data import Bar
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import Order, OrderFill
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.actors.signal_aggregator_actor import SignalContribution
from qts.runtime.session import RuntimeSessionResult
from qts.runtime.state import RuntimeSessionState


class RuntimeMarketDataCoordinator:
    """Own market-data source events and strategy/order actor coordination."""

    def __init__(self, session: Any) -> None:
        self._session = session

    def on_market_data_source_event(
        self,
        event: Bar
        | StreamingMarketDataDegradation
        | StreamingMarketDataSubscriptionEvent
        | MarketDataPermissionEvent,
    ) -> RuntimeSessionResult:
        """Handle a source market-data event, including degradation and permission signals."""
        session = self._session
        if isinstance(event, Bar):
            return self.on_market_data(event)
        flow_result = session._market_data_flow.publish_source_event(event)
        reason_code: str | None = None
        for runtime_event in flow_result.runtime_events:
            session._write(runtime_event)
            if runtime_event.kind == "runtime.degraded":
                if session.state is not RuntimeSessionState.DEGRADED:
                    session.degrade()
                reason_code = "RUNTIME_DEGRADED"
        primary_snapshot = session._primary_partition.account_actor.snapshot()
        account_snapshots = tuple(
            (account_id, partition.account_actor.snapshot())
            for account_id, partition in session._account_partitions.items()
        )
        return RuntimeSessionResult(
            market_data=(),
            orders=(),
            fills=(),
            account_snapshot=primary_snapshot,
            account_snapshots=account_snapshots,
            reason_code=reason_code,
        )

    def on_market_data(self, source_bar: Bar) -> RuntimeSessionResult:
        """Handle one source bar through market-data, strategy, risk, and actors."""
        session = self._session
        if (
            session._topology is not None
            and source_bar.instrument_id not in session._strategy_subscriptions
        ):
            snapshots = tuple(
                (account_id, partition.account_actor.snapshot())
                for account_id, partition in session._account_partitions.items()
            )
            return RuntimeSessionResult(
                market_data=(),
                orders=(),
                fills=(),
                account_snapshot=session._primary_partition.account_actor.snapshot(),
                account_snapshots=snapshots,
                reason_code="INSTRUMENT_NOT_SUBSCRIBED",
            )

        flow_result = session._market_data_flow.publish_source_event(source_bar)
        for event in flow_result.runtime_events:
            session._write(event)
            if (
                event.kind == "runtime.degraded"
                and session.state is not RuntimeSessionState.DEGRADED
            ):
                session.degrade()

        bars = flow_result.market_data
        all_orders: list[Order] = []
        all_fills: list[OrderFill] = []
        reason_code: str | None = None
        account_snapshots: tuple[tuple[AccountId | None, AccountSnapshot], ...]
        for bar in bars:
            correlation_id = CorrelationId(
                f"md:{bar.instrument_id.value}:{bar.timeframe}:{bar.end_time.isoformat()}"
            )
            session._latest_prices[bar.instrument_id] = bar.close
            session._write_event(
                "runtime.market_data",
                {
                    "instrument_id": bar.instrument_id.value,
                    "timeframe": bar.timeframe,
                    "end_time": bar.end_time.isoformat(),
                },
                correlation_id=correlation_id,
                instrument_id=bar.instrument_id,
            )
            blocked_reason = session._blocked_reason()
            if blocked_reason is not None:
                reason_code = blocked_reason
                continue

            bindings_for_bar = [
                binding
                for binding in session._strategy_bindings
                if binding.enabled
                and (not binding.subscriptions or bar.instrument_id in binding.subscriptions)
            ]
            if session._topology is not None and not bindings_for_bar:
                reason_code = "INSTRUMENT_NOT_SUBSCRIBED"
                continue

            aggregate_signals = session._event_index >= session._dependencies.warmup_bars
            contributions_by_account: dict[AccountId | None, list[SignalContribution]] = {}
            for binding in bindings_for_bar:
                strategy_result = binding.pipeline.execute_bar(
                    bar,
                    account_snapshot=session._resolve_partition(
                        binding.account_id
                    ).account_actor.snapshot(),
                    latest_prices=session._latest_prices,
                    aggregate_signals=aggregate_signals,
                )
                for intent in strategy_result.raw_intents:
                    session._write_event(
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
                    session._write_event(
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
                    if aggregate_signals:
                        contributions_by_account.setdefault(
                            binding.account_id,
                            [],
                        ).append(
                            SignalContribution(
                                strategy_id=binding.strategy_id,
                                intent=intent,
                                aggregation_policy=binding.signal_aggregation_policy,
                                priority=binding.signal_priority,
                                weight=binding.signal_weight,
                                conflict_group=binding.conflict_group,
                            )
                        )

            if aggregate_signals:
                for account_id, contributions in contributions_by_account.items():
                    partition = session._resolve_partition(account_id)
                    aggregated_batches = session._aggregate_signal_batches(
                        bar,
                        tuple(contributions),
                    )
                    for batch in aggregated_batches:
                        if batch.conflict_reason:
                            session._write_event(
                                "runtime.signal_conflict_detected",
                                {
                                    "conflict_reason": batch.conflict_reason,
                                    "rejected_strategy_ids": [
                                        strategy_id.value
                                        for strategy_id in batch.rejected_strategy_ids
                                    ],
                                    "conflict_group": batch.conflict_group,
                                    "aggregation_policy": batch.aggregation_policy.value,
                                },
                                correlation_id=correlation_id,
                                account_id=partition.account_id,
                                instrument_id=bar.instrument_id,
                            )
                            session._write_event(
                                "runtime.signal_rejected",
                                {
                                    "conflict_reason": batch.conflict_reason,
                                    "rejected_strategy_ids": [
                                        strategy_id.value
                                        for strategy_id in batch.rejected_strategy_ids
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
                                account_id=partition.account_id,
                                instrument_id=bar.instrument_id,
                            )
                        session._write_event(
                            "runtime.signal_aggregated",
                            {
                                "aggregation_policy": batch.aggregation_policy.value,
                                "contributing_strategy_ids": [
                                    strategy_id.value
                                    for strategy_id in batch.contributing_strategy_ids
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
                            account_id=partition.account_id,
                            instrument_id=bar.instrument_id,
                        )
                        if not batch.intents:
                            continue
                        if not session._dependencies.order_submission_enabled:
                            reason_code = "ORDER_SUBMISSION_DISABLED"
                            continue
                        for intent in batch.intents:
                            strategy_id = (
                                batch.contributing_strategy_ids[0]
                                if batch.contributing_strategy_ids
                                else session._resolved_strategy_id
                            )
                            if strategy_id is None:
                                raise ValueError("strategy_id is required")
                            processed = session._process_intent(
                                intent,
                                bar=bar,
                                account_id=account_id,
                                strategy_id=strategy_id,
                                correlation_id=correlation_id,
                                partition=partition,
                                contributing_strategy_ids=batch.contributing_strategy_ids,
                            )
                            all_orders.extend(processed.orders)
                            all_fills.extend(processed.fills)
                            self._write_risk_rejection_events(
                                processed.risk_decisions,
                                correlation_id=correlation_id,
                                account_id=partition.account_id,
                                instrument_id=intent.asset.instrument_id,
                                strategy_id=strategy_id,
                            )
                            self._write_order_events(
                                processed.orders,
                                partition=partition,
                                contributing_strategy_ids=batch.contributing_strategy_ids,
                            )
                            self._write_fill_events(processed.fills, partition=partition)

            session._event_index += 1

        primary_snapshot = session._primary_partition.account_actor.snapshot()
        account_snapshots = tuple(
            (account_id, partition.account_actor.snapshot())
            for account_id, partition in session._account_partitions.items()
        )
        if bars:
            self._write_account_snapshots()
        return RuntimeSessionResult(
            market_data=bars,
            orders=tuple(all_orders),
            fills=tuple(all_fills),
            account_snapshot=primary_snapshot,
            account_snapshots=account_snapshots,
            reason_code=reason_code,
        )

    def _write_risk_rejection_events(
        self,
        risk_decisions: tuple[RiskDecision, ...],
        *,
        correlation_id: CorrelationId,
        account_id: AccountId | None,
        instrument_id: InstrumentId,
        strategy_id: StrategyId,
    ) -> None:
        session = self._session
        for decision in risk_decisions:
            if decision.approved:
                continue
            session._write_event(
                "runtime.risk_rejected",
                {
                    "reason_code": decision.reason_code,
                    "reason": decision.reason,
                    "rule_id": decision.rule_id,
                    "evidence": dict(decision.evidence),
                },
                correlation_id=correlation_id,
                account_id=account_id,
                instrument_id=instrument_id,
                strategy_id=strategy_id,
            )

    def _write_order_events(
        self,
        orders: tuple[Order, ...],
        *,
        partition: Any,
        contributing_strategy_ids: tuple[StrategyId, ...],
    ) -> None:
        session = self._session
        for order in orders:
            metadata = partition.order_manager_actor.route_metadata(order.order_id)
            session._write_event(
                "runtime.order_submitted",
                {
                    "order_id": order.order_id.value,
                    "broker_order_id": order.broker_order_id,
                    "client_order_id": metadata.client_order_id,
                    "instrument_id": order.intent.instrument_id.value,
                    "contributing_strategy_ids": [
                        strategy_id.value for strategy_id in contributing_strategy_ids
                    ],
                },
                correlation_id=metadata.correlation_id,
                instrument_id=order.intent.instrument_id,
                strategy_id=metadata.strategy_id,
                account_id=metadata.account_id,
            )
            session._write_event(
                "runtime.broker_report",
                {
                    "order_id": order.order_id.value,
                    "state": order.state.value,
                    "broker_order_id": order.broker_order_id,
                    "client_order_id": metadata.client_order_id,
                },
                correlation_id=metadata.correlation_id,
                instrument_id=order.intent.instrument_id,
                strategy_id=metadata.strategy_id,
                account_id=metadata.account_id,
                causation_id=CausationId(f"{metadata.client_order_id}:order_submitted"),
            )

    def _write_fill_events(self, fills: tuple[OrderFill, ...], *, partition: Any) -> None:
        session = self._session
        for fill in fills:
            metadata = partition.order_manager_actor.route_metadata(fill.order_id)
            order = partition.order_manager_actor.get_order(fill.order_id)
            session._write_event(
                "runtime.fill_applied",
                {
                    "fill_id": fill.fill_id,
                    "order_id": fill.order_id.value,
                    "broker_order_id": order.broker_order_id,
                    "client_order_id": metadata.client_order_id,
                    "instrument_id": fill.instrument_id.value,
                    "side": fill.side.value,
                    "quantity": str(fill.quantity),
                    "price": str(fill.price),
                    "commission": str(fill.commission),
                    "slippage": str(fill.slippage),
                },
                correlation_id=metadata.correlation_id,
                instrument_id=fill.instrument_id,
                strategy_id=metadata.strategy_id,
                account_id=metadata.account_id,
                causation_id=CausationId(f"{metadata.client_order_id}:broker_report"),
            )

    def _write_account_snapshots(self) -> None:
        session = self._session
        for partition in session._account_partitions.values():
            snapshot = partition.account_actor.snapshot()
            session._write_event(
                "runtime.account_snapshot",
                {
                    "cash": {currency: str(balance) for currency, balance in snapshot.cash.items()},
                    "positions": {
                        instrument_id.value: str(position.quantity)
                        for instrument_id, position in snapshot.positions.items()
                    },
                },
                account_id=partition.account_id,
            )


__all__ = ["RuntimeMarketDataCoordinator"]
