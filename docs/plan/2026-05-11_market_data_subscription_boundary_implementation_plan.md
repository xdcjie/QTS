# Market Data Subscription Boundary Implementation Plan

> **For implementation workers:** implement this plan task-by-task. Read
> `AGENTS.md`, relevant module `AGENTS.md` files, and the referenced docs before
> each task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared market data subscription boundary for logical
subscriptions, provider-capability physical subscriptions, internal bar
aggregation, historical replay service, and fan-out.

**Architecture:** Keep provider capability and source I/O in `qts.data`, while
`MarketDataActor` owns subscription deduplication, aggregation state, and
subscriber fan-out. Backtest historical data and live/fake data sources produce
the same normalized actor-facing events.

**Tech Stack:** Python 3.11 dataclasses and protocols, existing `qts.data`,
`qts.runtime`, `qts.domain.market_data`, `BarAggregator`, `pytest`, `ruff`,
`mypy`.

---

## Source Documents

- `docs/README.md`
- `docs/architecture/system_overview.md`
- `docs/architecture/backtest_live_parity.md`
- `docs/domain/bar_timeframe_model.md`
- `docs/runtime/actor_model.md`
- `docs/testing/testing_strategy.md`
- `docs/testing/domain_invariants.md`

## File Structure

- Modify `backend/src/qts/data/live_feed.py`: add source timeframe selection to
  `FeedCapabilities`.
- Create `backend/src/qts/data/subscriptions.py`: logical and physical
  subscription keys plus planning rules that map requested timeframe to source
  timeframe.
- Create `backend/src/qts/data/historical/service.py`: historical market data
  service that exposes feed-like capabilities and deterministic replay events.
- Modify `backend/src/qts/data/historical/__init__.py`: export the historical
  service types.
- Modify `backend/src/qts/data/__init__.py`: export subscription planning types.
- Modify `backend/src/qts/runtime/actors/market_data_actor.py`: add
  subscription messages, physical subscription deduplication, per-logical
  subscribers, and multi-target aggregation fan-out.
- Add `tests/unit/data/test_subscription_planning.py`: unit coverage for
  requested-to-source timeframe planning.
- Extend `tests/unit/data/test_live_feed_contract.py`: capability behavior and
  fake feed subscription count.
- Add `tests/unit/data/test_historical_market_data_adapter.py`: historical
  service capability checks and deterministic replay.
- Extend `tests/unit/runtime/test_market_data_actor.py`: message-driven
  subscription deduplication, aggregation, and fan-out.
- Add `tests/anchor/test_market_data_subscription_anchors.py`: durable
  subscription/timeframe invariants.
- Extend `tests/integration/test_backtest_live_parity_flow.py`: historical and
  fake live sources use the same actor-facing event contract.

## Design Notes

Use these key shapes consistently:

```python
LogicalSubscriptionKey = (instrument_id, requested_timeframe)
PhysicalSubscriptionKey = (source_id, instrument_id, stream_type, source_timeframe)
AggregationKey = (instrument_id, source_timeframe, target_timeframe, session_id)
```

The first implementation supports bar subscriptions. Tick and quote subscription
objects can exist as stream-type values, but no new tick/quote behavior is
required beyond existing event forwarding.

`1d` remains out of scope for streaming aggregation in this increment because
the current `BarAggregator` supports clock-aligned targets only. Planning may
parse `1d`, but actor aggregation should continue to reject unsupported session
aggregation until a daily session aggregator exists.

---

## Task 1: Subscription Planning Model

**Files:**
- Create: `backend/src/qts/data/subscriptions.py`
- Modify: `backend/src/qts/data/live_feed.py`
- Modify: `backend/src/qts/data/__init__.py`
- Test: `tests/unit/data/test_subscription_planning.py`
- Test: `tests/unit/data/test_live_feed_contract.py`

- [ ] **Step 1: Write failing tests for provider capability planning**

Add `tests/unit/data/test_subscription_planning.py`:

```python
from __future__ import annotations

from qts.core.ids import InstrumentId
from qts.data.live import FeedCapabilities
from qts.data.subscriptions import (
    LogicalSubscription,
    PhysicalSubscriptionKey,
    SourceStreamType,
    plan_physical_subscription,
)


def test_ibkr_style_capability_maps_requested_minutes_to_single_5s_source() -> None:
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    capabilities = FeedCapabilities(
        source_id="ibkr-live-md",
        supports_bars=True,
        supported_timeframes=frozenset({"5s"}),
    )

    one_minute = plan_physical_subscription(
        LogicalSubscription(
            subscriber_id="strategy-a",
            instrument_id=instrument_id,
            requested_timeframe="1m",
        ),
        capabilities=capabilities,
    )
    five_minutes = plan_physical_subscription(
        LogicalSubscription(
            subscriber_id="strategy-b",
            instrument_id=instrument_id,
            requested_timeframe="5m",
        ),
        capabilities=capabilities,
    )

    expected = PhysicalSubscriptionKey(
        source_id="ibkr-live-md",
        instrument_id=instrument_id,
        stream_type=SourceStreamType.BAR,
        source_timeframe="5s",
    )
    assert one_minute == expected
    assert five_minutes == expected
```

Extend `tests/unit/data/test_live_feed_contract.py`:

```python
def test_feed_capabilities_choose_source_timeframe_for_derived_bar_request() -> None:
    capabilities = FeedCapabilities(
        source_id="ibkr-live",
        supported_timeframes=frozenset({"5s"}),
    )

    assert capabilities.source_timeframe_for("1m") == "5s"
    assert capabilities.source_timeframe_for("5m") == "5s"


def test_fake_live_feed_exposes_configured_capabilities_and_subscription_count() -> None:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    adapter = FakeLiveFeedAdapter(
        source_id="fake-live",
        capabilities=FeedCapabilities(
            source_id="fake-live",
            supported_timeframes=frozenset({"5s"}),
        ),
    )

    adapter.subscribe(FeedSubscription("sub-1", instrument_id, timeframe="5s"))
    adapter.subscribe(FeedSubscription("sub-1", instrument_id, timeframe="5s"))

    assert adapter.capabilities.source_timeframe_for("1m") == "5s"
    assert adapter.subscription_count == 1
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest tests/unit/data/test_subscription_planning.py \
  tests/unit/data/test_live_feed_contract.py::test_feed_capabilities_choose_source_timeframe_for_derived_bar_request -q
```

Expected: failures for missing `qts.data.subscriptions`,
`FeedCapabilities.source_timeframe_for`, `FakeLiveFeedAdapter.capabilities`
configuration, or `FakeLiveFeedAdapter.subscription_count`.

- [ ] **Step 3: Implement minimal subscription planning**

Create `backend/src/qts/data/subscriptions.py`:

```python
"""Market data subscription planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qts.core.ids import InstrumentId
from qts.data.live import FeedCapabilities


class SourceStreamType(StrEnum):
    BAR = "bar"
    TICK = "tick"
    QUOTE = "quote"


@dataclass(frozen=True, slots=True)
class LogicalSubscription:
    subscriber_id: str
    instrument_id: InstrumentId
    requested_timeframe: str
    stream_type: SourceStreamType = SourceStreamType.BAR

    def __post_init__(self) -> None:
        if not self.subscriber_id.strip():
            raise ValueError("subscriber_id must not be empty")
        if not self.requested_timeframe.strip():
            raise ValueError("requested_timeframe must not be empty")


@dataclass(frozen=True, slots=True)
class LogicalSubscriptionKey:
    instrument_id: InstrumentId
    requested_timeframe: str
    stream_type: SourceStreamType = SourceStreamType.BAR


@dataclass(frozen=True, slots=True)
class PhysicalSubscriptionKey:
    source_id: str
    instrument_id: InstrumentId
    stream_type: SourceStreamType
    source_timeframe: str

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.source_timeframe.strip():
            raise ValueError("source_timeframe must not be empty")


def logical_key(subscription: LogicalSubscription) -> LogicalSubscriptionKey:
    return LogicalSubscriptionKey(
        instrument_id=subscription.instrument_id,
        requested_timeframe=subscription.requested_timeframe,
        stream_type=subscription.stream_type,
    )


def plan_physical_subscription(
    subscription: LogicalSubscription,
    *,
    capabilities: FeedCapabilities,
) -> PhysicalSubscriptionKey:
    if subscription.stream_type is not SourceStreamType.BAR:
        raise ValueError("only bar subscriptions are supported")
    return PhysicalSubscriptionKey(
        source_id=capabilities.source_id,
        instrument_id=subscription.instrument_id,
        stream_type=subscription.stream_type,
        source_timeframe=capabilities.source_timeframe_for(subscription.requested_timeframe),
    )


__all__ = [
    "LogicalSubscription",
    "LogicalSubscriptionKey",
    "PhysicalSubscriptionKey",
    "SourceStreamType",
    "logical_key",
    "plan_physical_subscription",
]
```

Modify `FeedCapabilities` in `backend/src/qts/data/live_feed.py`:

```python
    def source_timeframe_for(self, requested_timeframe: str) -> str:
        if not requested_timeframe.strip():
            raise ValueError("requested_timeframe must not be empty")
        if self.supports_timeframe(requested_timeframe):
            return requested_timeframe
        if "5s" in self.supported_timeframes and requested_timeframe in {
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "4h",
        }:
            return "5s"
        if "1m" in self.supported_timeframes and requested_timeframe in {
            "5m",
            "15m",
            "30m",
            "1h",
            "4h",
        }:
            return "1m"
        raise ValueError(
            f"requested timeframe {requested_timeframe} cannot be derived "
            f"from source {self.source_id}"
        )
```

Export the new types from `backend/src/qts/data/__init__.py`.

Modify `FakeLiveFeedAdapter` in `backend/src/qts/data/live_feed.py`:

```python
    def __init__(
        self,
        *,
        source_id: str,
        capabilities: FeedCapabilities | None = None,
    ) -> None:
        if not source_id.strip():
            raise ValueError("source_id must not be empty")
        if capabilities is not None and capabilities.source_id != source_id:
            raise ValueError("capabilities source_id must match adapter source_id")
        self._source_id = source_id
        self._capabilities = capabilities
        self._subscriptions: dict[str, FeedSubscription] = {}

    @property
    def capabilities(self) -> FeedCapabilities:
        return self._capabilities or FeedCapabilities(source_id=self._source_id)

    @property
    def subscription_count(self) -> int:
        return len(self._subscriptions)
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest tests/unit/data/test_subscription_planning.py \
  tests/unit/data/test_live_feed_contract.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/qts/data/live_feed.py backend/src/qts/data/subscriptions.py \
  backend/src/qts/data/__init__.py tests/unit/data/test_subscription_planning.py \
  tests/unit/data/test_live_feed_contract.py
git commit -m "feat: add market data subscription planning"
```

## Task 2: MarketDataActor Subscription Dedup And Fan-Out

**Files:**
- Modify: `backend/src/qts/runtime/actors/market_data_actor.py`
- Test: `tests/unit/runtime/test_market_data_actor.py`

- [ ] **Step 1: Write failing actor tests**

Extend `tests/unit/runtime/test_market_data_actor.py`:

```python
def test_market_data_actor_deduplicates_physical_subscription_and_fans_out() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.live import FakeLiveFeedAdapter, FeedCapabilities
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.market_data_actor import MarketDataActor, SubscribeMarketData
    from qts.runtime.mailbox import Mailbox

    source = FakeLiveFeedAdapter(
        source_id="ibkr-live-md",
        capabilities=FeedCapabilities(
            source_id="ibkr-live-md",
            supported_timeframes=frozenset({"5s"}),
        ),
    )
    left = Mailbox()
    right = Mailbox()
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    actor = MarketDataActor(
        feed=source,
        exchange_timezone="UTC",
    )

    actor.handle(
        SubscribeMarketData(
            subscriber_id="strategy-a",
            subscriber_ref=ActorRef(mailbox=left),
            instrument_id=instrument_id,
            timeframe="1m",
        )
    )
    actor.handle(
        SubscribeMarketData(
            subscriber_id="strategy-b",
            subscriber_ref=ActorRef(mailbox=right),
            instrument_id=instrument_id,
            timeframe="1m",
        )
    )

    assert source.subscription_count == 1
    assert actor.logical_subscription_count == 1
```

Add a second test that sends twelve `5s` bars and asserts one completed `1m`
bar is delivered to both subscriber mailboxes.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest tests/unit/runtime/test_market_data_actor.py::test_market_data_actor_deduplicates_physical_subscription_and_fans_out -q
```

Expected: failure for missing `SubscribeMarketData`, `feed` constructor
argument, or `subscription_count`.

- [ ] **Step 3: Implement message-driven subscription state**

Modify `backend/src/qts/runtime/actors/market_data_actor.py`:

```python
@dataclass(frozen=True, slots=True)
class SubscribeMarketData:
    subscriber_id: str
    subscriber_ref: ActorRef
    instrument_id: InstrumentId
    timeframe: str
```

Add optional `feed: LiveFeedAdapter | None = None` to the constructor. Store:

```python
self._feed = feed
self._logical_subscribers: dict[LogicalSubscriptionKey, list[ActorRef]] = {}
self._physical_subscriptions: set[PhysicalSubscriptionKey] = set()
self._aggregators: dict[tuple[InstrumentId, str, str, str], BarAggregator] = {}
```

On `SubscribeMarketData`:

1. Build `LogicalSubscription`.
2. Add the subscriber to `self._logical_subscribers[logical_key]` if not already present.
3. If `feed` exists, compute `PhysicalSubscriptionKey`.
4. If the physical key is new, call `feed.subscribe(FeedSubscription(
   subscription_id=f"{source_id}:{instrument_id.value}:{source_timeframe}",
   instrument_id=instrument_id,
   timeframe=source_timeframe,
))` once.

On `MarketDataEvent` containing a `Bar`, publish to all direct logical subscribers
matching the bar timeframe. For requested higher timeframes, update the
matching `BarAggregator` once per `(instrument, source_timeframe,
target_timeframe, session)` and publish completed bars only to that logical
timeframe's subscribers.

Keep the old constructor behavior with `subscribers` and `aggregate_timeframe`
for compatibility with existing tests.

- [ ] **Step 4: Run actor tests to verify GREEN**

Run:

```bash
uv run pytest tests/unit/runtime/test_market_data_actor.py -q
```

Expected: all actor tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/qts/runtime/actors/market_data_actor.py \
  tests/unit/runtime/test_market_data_actor.py
git commit -m "feat: deduplicate market data actor subscriptions"
```

## Task 3: Historical Market Data Service

**Files:**
- Create: `backend/src/qts/data/historical/service.py`
- Modify: `backend/src/qts/data/historical/__init__.py`
- Test: `tests/unit/data/test_historical_market_data_adapter.py`

- [ ] **Step 1: Write failing historical adapter tests**

Add `tests/unit/data/test_historical_market_data_adapter.py` with deterministic
CSV fixture rows. Test:

```python
def test_historical_market_data_adapter_replays_normalized_bars_for_subscription(
    tmp_path: Path,
) -> None:
    adapter = HistoricalMarketDataAdapter(
        source_id="historical-gc",
        csv_path=csv_path,
        symbol_resolver=StaticSymbolResolver({"GCQ0": InstrumentId("FUTURE.CME.GC.GCQ0")}),
        source_timeframe="1m",
        start=start,
        end=start + timedelta(minutes=2),
    )
    subscription = FeedSubscription(
        subscription_id="hist-1",
        instrument_id=InstrumentId("FUTURE.CME.GC.GCQ0"),
        timeframe="1m",
    )

    subscribed = adapter.subscribe(subscription)
    events = tuple(adapter.events(subscription.subscription_id))

    assert subscribed.source_id == "historical-gc"
    assert [event.source_id for event in events] == ["historical-gc", "historical-gc"]
    assert [event.payload.instrument_id for event in events] == [subscription.instrument_id] * 2
```

Add a second test:

```python
def test_historical_market_data_adapter_rejects_finer_than_source_request() -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    adapter = HistoricalMarketDataAdapter(
        source_id="historical-gc",
        csv_path=csv_path,
        symbol_resolver=StaticSymbolResolver({"GCQ0": instrument_id}),
        source_timeframe="1m",
        start=start,
        end=start + timedelta(minutes=1),
    )

    with pytest.raises(ValueError, match="cannot be derived"):
        adapter.subscribe(FeedSubscription("hist-5s", instrument_id, timeframe="5s"))
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest tests/unit/data/test_historical_market_data_adapter.py -q
```

Expected: failure for missing `qts.data.historical.adapter`.

- [ ] **Step 3: Implement minimal historical adapter**

Create `backend/src/qts/data/historical/adapter.py`:

```python
"""Historical market data source adapter."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.csv_dataset import iter_historical_bars
from qts.data.live import FeedCapabilities, FeedSubscription, LiveFeedEvent, MarketDataSubscribed
from qts.registry.symbol_resolution import SourceSymbolResolver


@dataclass(frozen=True, slots=True)
class HistoricalMarketDataAdapter:
    source_id: str
    csv_path: Path
    symbol_resolver: SourceSymbolResolver
    source_timeframe: str
    start: datetime | None = None
    end: datetime | None = None

    @property
    def capabilities(self) -> FeedCapabilities:
        return FeedCapabilities(
            source_id=self.source_id,
            supports_ticks=False,
            supports_quotes=False,
            supports_bars=True,
            supported_timeframes=frozenset({self.source_timeframe}),
        )

    def subscribe(self, subscription: FeedSubscription) -> MarketDataSubscribed:
        self.capabilities.source_timeframe_for(subscription.timeframe)
        return MarketDataSubscribed(subscription=subscription, source_id=self.source_id)

    def events(self, subscription_id: str) -> Iterator[LiveFeedEvent]:
        if not subscription_id.strip():
            raise ValueError("subscription_id must not be empty")
        stream = iter_historical_bars(
            self.csv_path,
            self.symbol_resolver,
            timeframe=self.source_timeframe,
            start=self.start,
            end=self.end,
        )
        for bar in stream:
            yield LiveFeedEvent(payload=bar, source_id=self.source_id)
```

Export `HistoricalMarketDataAdapter` from
`backend/src/qts/data/historical/__init__.py`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest tests/unit/data/test_historical_market_data_adapter.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/qts/data/historical/adapter.py \
  backend/src/qts/data/historical/__init__.py \
  tests/unit/data/test_historical_market_data_adapter.py
git commit -m "feat: add historical market data adapter"
```

## Task 4: Anchor And Integration Coverage

**Files:**
- Create: `tests/anchor/test_market_data_subscription_anchors.py`
- Modify: `tests/integration/test_backtest_live_parity_flow.py`

- [ ] **Step 1: Write anchor tests**

Add `tests/anchor/test_market_data_subscription_anchors.py`:

```python
from __future__ import annotations

from qts.core.ids import InstrumentId
from qts.data.live import FeedCapabilities
from qts.data.subscriptions import LogicalSubscription, plan_physical_subscription


def test_provider_5s_source_does_not_redefine_requested_1m_bar_semantics() -> None:
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    capabilities = FeedCapabilities(
        source_id="ibkr-live-md",
        supported_timeframes=frozenset({"5s"}),
    )

    physical = plan_physical_subscription(
        LogicalSubscription("strategy-a", instrument_id, "1m"),
        capabilities=capabilities,
    )

    assert physical.source_timeframe == "5s"
```

Add anchor assertions that a `1m` source rejects `5s`, and that two logical
requests for `1m` and `5m` share the same physical `5s` key.

- [ ] **Step 2: Write integration parity test**

Extend `tests/integration/test_backtest_live_parity_flow.py` with a test that
creates a `FakeLiveFeedAdapter` and a `HistoricalMarketDataAdapter`, subscribes
to each, emits or replays one `Bar`, and sends both through `MarketDataActor`
as `MarketDataEvent`.

Assert both paths deliver a normalized `Bar` with the same `InstrumentId` and
no source symbol field.

- [ ] **Step 3: Run tests after Tasks 1-3**

Run:

```bash
uv run pytest tests/anchor/test_market_data_subscription_anchors.py \
  tests/integration/test_backtest_live_parity_flow.py -q
```

Expected before implementation: missing types fail. Expected after Tasks 1-3:
tests pass or expose small integration wiring gaps to fix.

- [ ] **Step 4: Fix integration wiring only if needed**

Do not add new behavior beyond making historical and fake live sources use the
same actor-facing message contract.

- [ ] **Step 5: Commit**

```bash
git add tests/anchor/test_market_data_subscription_anchors.py \
  tests/integration/test_backtest_live_parity_flow.py
git commit -m "test: anchor market data subscription semantics"
```

## Task 5: Final Verification

**Files:**
- No new files unless a check exposes a necessary narrow fix.

- [ ] **Step 1: Run formatting**

```bash
make format
```

Expected: exits `0`.

- [ ] **Step 2: Run lint**

```bash
make lint
```

Expected: exits `0`.

- [ ] **Step 3: Run typecheck**

```bash
make typecheck
```

Expected: exits `0`.

- [ ] **Step 4: Run unit tests**

```bash
make test-unit
```

Expected: exits `0`.

- [ ] **Step 5: Run integration tests**

```bash
make test-integration
```

Expected: exits `0`.

- [ ] **Step 6: Run anchor tests**

```bash
make test-anchor
```

Expected: exits `0`.

- [ ] **Step 7: Report outcome**

Final response must include changed files, checks run, checks not run, and any
known limitations. Note that full multi-strategy backtest execution remains out
of scope for this boundary increment.

## Self-Review Checklist

- Subscription planning covers provider `5s` -> requested `1m`/`5m` derivation.
- Historical `1m` source rejects requested `5s`.
- `MarketDataActor` owns subscriber lists and aggregation state.
- Provider/source symbols stay outside runtime actor messages.
- No new top-level docs directory is introduced.
- No backtest-only aggregation path is introduced.
