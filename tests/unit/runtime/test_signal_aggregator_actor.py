from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.strategy_sdk import TargetIntent


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


def test_sum_targets_same_direction() -> None:
    from qts.core.ids import StrategyId
    from qts.runtime.signal_policy import (
        SignalAggregationPolicy,
        SignalContribution,
        SignalPolicyEngine,
    )

    left = _quantity_intent(Decimal("10"))
    right = _quantity_intent(Decimal("5"))

    decision = SignalPolicyEngine(policy=SignalAggregationPolicy.SUM_TARGETS).aggregate(
        (
            SignalContribution(strategy_id=StrategyId("strategy-a"), intent=left),
            SignalContribution(strategy_id=StrategyId("strategy-b"), intent=right),
        )
    )

    assert len(decision.intents) == 1
    assert decision.intents[0].value == Decimal("15")
    assert decision.contributing_strategy_ids == (
        StrategyId("strategy-a"),
        StrategyId("strategy-b"),
    )


def test_reject_conflicting_targets() -> None:
    from qts.core.ids import StrategyId
    from qts.runtime.signal_policy import (
        SignalAggregationPolicy,
        SignalContribution,
        SignalPolicyEngine,
    )

    decision = SignalPolicyEngine(policy=SignalAggregationPolicy.REJECT_CONFLICT).aggregate(
        (
            SignalContribution(strategy_id=StrategyId("strategy-a"), intent=_quantity_intent(10)),
            SignalContribution(strategy_id=StrategyId("strategy-b"), intent=_quantity_intent(-5)),
        )
    )

    assert decision.intents == ()
    assert decision.conflicts
    assert decision.rejected_strategy_ids == (
        StrategyId("strategy-a"),
        StrategyId("strategy-b"),
    )
    assert "opposite directions" in decision.conflict_reason


def test_priority_wins_conflicting_targets() -> None:
    from qts.core.ids import StrategyId
    from qts.runtime.signal_policy import (
        SignalAggregationPolicy,
        SignalContribution,
        SignalPolicyEngine,
    )

    decision = SignalPolicyEngine(policy=SignalAggregationPolicy.PRIORITY_WINS).aggregate(
        (
            SignalContribution(
                strategy_id=StrategyId("strategy-low"),
                intent=_quantity_intent(10),
                priority=1,
            ),
            SignalContribution(
                strategy_id=StrategyId("strategy-high"),
                intent=_quantity_intent(-5),
                priority=10,
            ),
        )
    )

    assert len(decision.intents) == 1
    assert decision.intents[0].value == Decimal("-5")
    assert decision.contributing_strategy_ids == (StrategyId("strategy-high"),)
    assert decision.rejected_strategy_ids == (StrategyId("strategy-low"),)


def test_weighted_net_targets() -> None:
    from qts.core.ids import StrategyId
    from qts.runtime.signal_policy import (
        SignalAggregationPolicy,
        SignalContribution,
        SignalPolicyEngine,
    )

    decision = SignalPolicyEngine(policy=SignalAggregationPolicy.WEIGHTED_NET).aggregate(
        (
            SignalContribution(
                strategy_id=StrategyId("strategy-a"),
                intent=_quantity_intent(10),
                weight=Decimal("0.5"),
            ),
            SignalContribution(
                strategy_id=StrategyId("strategy-b"),
                intent=_quantity_intent(-5),
                weight=Decimal("0.2"),
            ),
        )
    )

    assert len(decision.intents) == 1
    assert decision.intents[0].value == Decimal("4.0")
    assert decision.target_after_aggregation == Decimal("4.0")


def _quantity_intent(value: Decimal | int) -> TargetIntent:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef, TargetIntent
    from qts.strategy_sdk.target import TargetIntentType

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    return TargetIntent(
        asset=AssetRef(instrument_id=instrument_id, symbol="AAPL"),
        intent_type=TargetIntentType.QUANTITY,
        value=Decimal(value),
    )
