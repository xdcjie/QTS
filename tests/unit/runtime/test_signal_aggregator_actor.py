from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal


def test_signal_aggregator_actor_emits_strategy_intents_for_order_flow() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.signal_aggregator_actor import (
        AggregatedSignalBatch,
        SignalAggregatorActor,
        StrategySignalEvent,
    )
    from qts.runtime.mailbox import Mailbox
    from qts.strategy_sdk import AssetRef, TargetIntent
    from qts.strategy_sdk.target import TargetIntentType

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bar = Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        is_complete=True,
    )
    intent = TargetIntent(
        asset=AssetRef(instrument_id=instrument_id, symbol="AAPL"),
        intent_type=TargetIntentType.QUANTITY,
        value=Decimal("2"),
    )
    outbox = Mailbox()
    actor = SignalAggregatorActor(result_ref=ActorRef(mailbox=outbox))

    actor.handle(StrategySignalEvent(bar=bar, intents=(intent,)))

    result = outbox.get()
    assert isinstance(result, AggregatedSignalBatch)
    assert result.bar == bar
    assert result.intents == (intent,)
    assert outbox.empty()
