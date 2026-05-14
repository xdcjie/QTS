"""Runtime orchestration for market data delivery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo

from qts.core.ids import InstrumentId
from qts.data.permissions import MarketDataPermissionEvent
from qts.data.sources.streaming_market_data_source import StreamingMarketDataDegradation
from qts.domain.market_data import Bar
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

    def publish_bar(self, bar: Bar) -> tuple[Bar, ...]:
        """Publish one source bar through the market data actor boundary."""
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
        event: Bar | StreamingMarketDataDegradation | MarketDataPermissionEvent,
    ) -> MarketDataFlowResult:
        """Publish a source event through runtime market-data orchestration."""

        if isinstance(event, Bar):
            return MarketDataFlowResult(market_data=self.publish_bar(event))
        if isinstance(event, StreamingMarketDataDegradation):
            return MarketDataFlowResult(runtime_events=(self._runtime_degradation_event(event),))
        if isinstance(event, MarketDataPermissionEvent):
            return MarketDataFlowResult(runtime_events=(self._runtime_permission_event(event),))
        raise TypeError(f"unsupported market data source event: {type(event).__name__}")

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
    def _runtime_degradation_event(
        degradation: StreamingMarketDataDegradation,
    ) -> RuntimeEvent:
        """Convert data-source stale signals to runtime degradation events."""

        return RuntimeEvent(
            kind="runtime.degraded",
            payload={
                "reason": degradation.reason,
                "instrument_id": degradation.instrument_id.value,
                "requested_timeframe": degradation.subscription.requested_timeframe,
                "stream_type": degradation.subscription.stream_type.value,
                "age_seconds": degradation.age.total_seconds(),
                "max_age_seconds": degradation.max_age.total_seconds(),
                "observed_at": degradation.observed_at.isoformat(),
            },
        )

    @staticmethod
    def _runtime_permission_event(event: MarketDataPermissionEvent) -> RuntimeEvent:
        """Convert provider permission callbacks to runtime events."""

        return RuntimeEvent(
            kind="market_data_permission_changed",
            payload={
                "source_id": event.source_id,
                "permission_state": event.permission_state.value,
                "provider_market_data_type": event.provider_market_data_type,
                "request_id": event.request_id,
            },
        )


__all__ = ["MarketDataFlow", "MarketDataFlowResult"]
