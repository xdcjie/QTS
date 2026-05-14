from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from qts.api.app import create_app
from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
from qts.data.live_feed import FeedSubscription
from qts.domain.market_data import Bar
from qts.execution.broker import BrokerOrderRequest, FakeBrokerAdapter
from qts.execution.order_manager import OrderSide
from qts.reconciliation import OrderSnapshot, ReconciliationSnapshot, reconcile_snapshots
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
from qts.runtime.live import LiveRuntime
from qts.runtime.mailbox import Mailbox

from tests.support.live_feed import FakeLiveFeedAdapter


def test_live_runtime_start_pause_resume_and_fake_broker_flow() -> None:
    runtime = LiveRuntime(
        broker=FakeBrokerAdapter(broker_id=BrokerId("fake")),
        feed=FakeLiveFeedAdapter(source_id="fake-live"),
    )
    runtime.start()
    runtime.pause()

    blocked = runtime.submit_order(
        BrokerOrderRequest(
            order_id=OrderId("order-1"),
            account_id=AccountId("acct-a"),
            strategy_id=StrategyId("strat-a"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
        )
    )
    runtime.resume()
    accepted = runtime.submit_order(blocked.request)

    assert blocked.accepted is False
    assert blocked.reason_code == "RUNTIME_PAUSED"
    assert accepted.accepted is True


def test_live_feed_routes_through_market_data_actor_aggregation_pipeline() -> None:
    mailbox = Mailbox()
    actor = MarketDataActor(
        subscribers=(ActorRef(mailbox),),
        aggregate_timeframe="5m",
        exchange_timezone=UTC,
    )
    feed = FakeLiveFeedAdapter(source_id="fake-live")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    feed.subscribe(FeedSubscription("sub-1", instrument_id, timeframe="1m"))
    start = datetime(2026, 5, 10, 9, 30, tzinfo=UTC)

    for offset in range(5):
        bar = Bar(
            instrument_id=instrument_id,
            start_time=start + timedelta(minutes=offset),
            end_time=start + timedelta(minutes=offset + 1),
            timeframe="1m",
            session_id="2026-05-10",
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            is_complete=True,
        )
        actor.handle(MarketDataEvent(payload=feed.emit(bar).payload))

    assert mailbox.size == 1
    message = mailbox.get()
    assert isinstance(message, Bar)
    assert message.timeframe == "5m"


def test_reconciliation_report_emits_drift_without_mutating_snapshots() -> None:
    account_id = AccountId("acct-a")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    internal = ReconciliationSnapshot(
        account_id=account_id,
        orders=(
            OrderSnapshot(
                order_id=OrderId("order-1"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("1"),
                status="accepted",
            ),
        ),
    )
    broker = ReconciliationSnapshot(account_id=account_id)

    report = reconcile_snapshots(internal=internal, broker=broker)

    assert report.has_drift
    assert internal.orders[0].status == "accepted"


def test_operational_api_idempotency_and_kill_switch_endpoints() -> None:
    client = TestClient(create_app())

    first = client.post(
        "/operations/runtime/pause",
        headers={"Idempotency-Key": "pause-1", "X-QTS-Operator": "tester"},
    )
    duplicate = client.post(
        "/operations/runtime/pause",
        headers={"Idempotency-Key": "pause-1", "X-QTS-Operator": "tester"},
    )
    halt = client.post(
        "/operations/kill-switches",
        json={"scope": "global", "scope_id": None, "reason": "test halt"},
        headers={"X-QTS-Operator": "tester"},
    )

    assert first.status_code == 200
    assert duplicate.json() == first.json()
    assert halt.json()["active"] is True
