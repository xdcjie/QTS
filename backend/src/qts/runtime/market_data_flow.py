"""Runtime orchestration for market data delivery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo

from qts.core.ids import InstrumentId
from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
from qts.data.provenance import ReplayDataAnomalyEvent, ReplayDataAnomalyType
from qts.data.sources.streaming_market_data_source import (
    StreamingMarketDataDegradation,
    StreamingMarketDataSubscriptionEvent,
    StreamingMarketDataSubscriptionEventType,
)
from qts.domain.market_data import Bar
from qts.domain.risk import MarketDataRiskContext
from qts.observability.errors import OperationalErrorCode
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
from qts.runtime.mailbox import Mailbox
from qts.runtime.sinks.base import RuntimeEvent


@dataclass(frozen=True, slots=True)
class MarketDataFlowResult:
    """Runtime events produced by one source market-data event."""

    market_data: tuple[Bar, ...] = ()
    runtime_events: tuple[RuntimeEvent, ...] = ()


class MarketDataFlow:
    """Connect source bars to MarketDataActor and return actor-ready bars."""

    def __init__(
        self,
        *,
        target_timeframe: str | None,
        exchange_timezone_by_instrument: dict[InstrumentId, str | tzinfo],
    ) -> None:
        """Create runtime flow state for market data actor fan-out."""
        self._target_timeframe = target_timeframe
        self._exchange_timezone_by_instrument = dict(exchange_timezone_by_instrument)
        self._mailbox = Mailbox()
        self._subscriber = ActorRef(mailbox=self._mailbox)
        self._refs: dict[tuple[str | None, str | tzinfo | None], ActorRef] = {}
        self._permission_context = MarketDataRiskContext()
        self._stale_context_by_instrument: dict[InstrumentId, MarketDataRiskContext] = {}

    def publish_bar(self, bar: Bar) -> tuple[Bar, ...]:
        """Publish one source bar through the market data actor boundary."""
        self._stale_context_by_instrument.pop(bar.instrument_id, None)
        market_data_ref = self._market_data_ref_for(bar)
        market_data_ref.tell(MarketDataEvent(payload=bar))
        market_data_ref.process_all()
        ready: list[Bar] = []
        while not self._mailbox.empty():
            payload = self._mailbox.get()
            if not isinstance(payload, Bar):
                raise TypeError(f"unexpected market data payload: {type(payload).__name__}")
            ready.append(payload)
        return tuple(ready)

    def publish_source_event(
        self,
        event: Bar
        | StreamingMarketDataDegradation
        | StreamingMarketDataSubscriptionEvent
        | ReplayDataAnomalyEvent
        | MarketDataPermissionEvent,
    ) -> MarketDataFlowResult:
        """Publish a source event through runtime market-data orchestration."""

        if isinstance(event, Bar):
            return MarketDataFlowResult(market_data=self.publish_bar(event))
        if isinstance(event, StreamingMarketDataDegradation):
            self._stale_context_by_instrument[event.instrument_id] = MarketDataRiskContext(
                permission_state=self._permission_context.permission_state,
                stale=True,
                evidence=self._stale_data_payload(event),
            )
            return MarketDataFlowResult(runtime_events=self._runtime_degradation_events(event))
        if isinstance(event, StreamingMarketDataSubscriptionEvent):
            return MarketDataFlowResult(runtime_events=self._runtime_subscription_events(event))
        if isinstance(event, ReplayDataAnomalyEvent):
            return MarketDataFlowResult(runtime_events=self._runtime_replay_anomaly_events(event))
        if isinstance(event, MarketDataPermissionEvent):
            self._permission_context = MarketDataRiskContext(
                permission_state=event.permission_state.value,
                stale=False,
                evidence=self._permission_payload(event),
            )
            return MarketDataFlowResult(runtime_events=self._runtime_permission_events(event))
        raise TypeError(f"unsupported market data source event: {type(event).__name__}")

    def risk_context_for(self, instrument_id: InstrumentId) -> MarketDataRiskContext:
        """Return latest market-data permission/freshness context for an instrument."""
        stale_context = self._stale_context_by_instrument.get(instrument_id)
        if stale_context is None:
            return self._permission_context
        return MarketDataRiskContext(
            permission_state=stale_context.permission_state,
            stale=True,
            evidence={
                **self._permission_context.evidence_payload(),
                **stale_context.evidence_payload(),
            },
        )

    def _market_data_ref_for(self, bar: Bar) -> ActorRef:
        """Return the actor ref responsible for this bar's aggregation shape."""
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
        ref = self._refs.get(key)
        if ref is None:
            ref = ActorRef(
                actor=MarketDataActor(
                    subscribers=(self._subscriber,),
                    aggregate_timeframe=aggregate_timeframe,
                    exchange_timezone=exchange_timezone,
                ),
                mailbox=Mailbox(),
            )
            self._refs[key] = ref
        return ref

    @staticmethod
    def _runtime_degradation_events(
        degradation: StreamingMarketDataDegradation,
    ) -> tuple[RuntimeEvent, ...]:
        """Convert data-source stale signals to runtime degradation events."""

        payload = MarketDataFlow._stale_data_payload(degradation)
        return (
            RuntimeEvent(kind="market_data_stale_detected", payload=payload),
            RuntimeEvent(kind="runtime.degraded", payload=payload),
        )

    @staticmethod
    def _stale_data_payload(degradation: StreamingMarketDataDegradation) -> dict[str, object]:
        return {
            "reason": degradation.reason,
            "reason_code": OperationalErrorCode.MARKET_DATA_STALE.value,
            "instrument_id": degradation.instrument_id.value,
            "requested_timeframe": degradation.subscription.requested_timeframe,
            "stream_type": degradation.subscription.stream_type.value,
            "age_seconds": degradation.age.total_seconds(),
            "max_age_seconds": degradation.max_age.total_seconds(),
            "observed_at": degradation.observed_at.isoformat(),
        }

    @staticmethod
    def _runtime_permission_events(event: MarketDataPermissionEvent) -> tuple[RuntimeEvent, ...]:
        """Convert provider permission callbacks to runtime events."""

        permission_event = RuntimeEvent(
            kind="market_data_permission_changed",
            payload=MarketDataFlow._permission_payload(event),
        )
        if event.permission_state is MarketDataPermissionState.LIVE:
            return (permission_event,)
        return (
            permission_event,
            RuntimeEvent(
                kind="runtime.degraded",
                payload={
                    **MarketDataFlow._permission_payload(event),
                    "reason": "market_data_permission_not_live",
                    "reason_code": OperationalErrorCode.MARKET_DATA_PERMISSION_ERROR.value,
                },
            ),
        )

    @staticmethod
    def _runtime_subscription_events(
        event: StreamingMarketDataSubscriptionEvent,
    ) -> tuple[RuntimeEvent, ...]:
        """Convert source subscription lifecycle signals to runtime events."""

        lifecycle_event = RuntimeEvent(
            kind=MarketDataFlow._subscription_event_kind(event.event_type),
            payload=MarketDataFlow._subscription_payload(event),
        )
        if event.event_type is not StreamingMarketDataSubscriptionEventType.FAILED:
            return (lifecycle_event,)
        return (
            lifecycle_event,
            RuntimeEvent(
                kind="runtime.degraded",
                payload={
                    **MarketDataFlow._subscription_payload(event),
                    "reason": "market_data_subscription_failed",
                    "reason_code": OperationalErrorCode.MARKET_DATA_SUBSCRIPTION_FAILED.value,
                    "subscription_failure_reason": event.reason,
                },
            ),
        )

    @staticmethod
    def _runtime_replay_anomaly_events(event: ReplayDataAnomalyEvent) -> tuple[RuntimeEvent, ...]:
        """Convert replay data-quality diagnostics to runtime-visible events."""

        anomaly_event = RuntimeEvent(
            kind=event.anomaly_type.value,
            payload=MarketDataFlow._replay_anomaly_payload(event),
        )
        if event.anomaly_type not in {
            ReplayDataAnomalyType.GAP_DETECTED,
            ReplayDataAnomalyType.OUT_OF_ORDER_REJECTED,
            ReplayDataAnomalyType.DATA_SCHEMA_ERROR,
        }:
            return (anomaly_event,)
        return (
            anomaly_event,
            RuntimeEvent(
                kind="runtime.degraded",
                payload={
                    **MarketDataFlow._replay_anomaly_payload(event),
                    "reason": event.anomaly_type.value,
                },
            ),
        )

    @staticmethod
    def _subscription_event_kind(event_type: StreamingMarketDataSubscriptionEventType) -> str:
        return {
            StreamingMarketDataSubscriptionEventType.SUBSCRIBED: "market_data_subscribed",
            StreamingMarketDataSubscriptionEventType.UNSUBSCRIBED: "market_data_unsubscribed",
            StreamingMarketDataSubscriptionEventType.RESUBSCRIBED: "market_data_resubscribed",
            StreamingMarketDataSubscriptionEventType.FAILED: "market_data_subscription_failed",
        }[event_type]

    @staticmethod
    def _subscription_payload(
        event: StreamingMarketDataSubscriptionEvent,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_id": event.source_id,
            "instrument_id": event.instrument_id.value,
            "requested_timeframe": event.subscription.requested_timeframe,
            "stream_type": event.subscription.stream_type.value,
            "broker_symbol": event.broker_symbol,
            "observed_at": event.observed_at.isoformat(),
        }
        if event.reason is not None:
            payload["reason"] = event.reason
        return payload

    @staticmethod
    def _permission_payload(event: MarketDataPermissionEvent) -> dict[str, object]:
        return {
            "source_id": event.source_id,
            "permission_state": event.permission_state.value,
            "provider_market_data_type": event.provider_market_data_type,
            "request_id": event.request_id,
        }

    @staticmethod
    def _replay_anomaly_payload(event: ReplayDataAnomalyEvent) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_id": event.source_id,
            "instrument_id": event.instrument_id.value,
            "timeframe": event.timeframe,
            "bar_start": event.bar_start.isoformat(),
            "bar_end": event.bar_end.isoformat(),
            "observed_at": event.observed_at.isoformat(),
        }
        if event.previous_end is not None:
            payload["previous_end"] = event.previous_end.isoformat()
        if event.reason is not None:
            payload["detail"] = event.reason
        return payload


__all__ = ["MarketDataFlow", "MarketDataFlowResult"]
