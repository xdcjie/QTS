from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, StrategyId
from qts.domain.market_data import Bar
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import TargetIntent, TargetIntentType
from qts.strategy_sdk.asset_ref import AssetRef


def _bar(start: datetime, close: str = "100") -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def _asset() -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        symbol="AAPL",
    )


def _new_environment(
    *, bar: Bar
) -> tuple[Any, OrderManagerActor, ActorRef, ActorRef, AccountActor, ActorRef]:
    from qts.backtest.engine import BacktestCostModel
    from qts.backtest.instrument_context import BacktestInstrumentContext
    from qts.backtest.portfolio_projection import BacktestPortfolioProjector
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.intent_processing import TargetIntentProcessor

    account_actor = AccountActor(initial_cash={"USD": Decimal("10000")})
    account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
    execution_mailbox = Mailbox()
    order_manager_actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=account_ref,
    )
    order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=Mailbox())
    execution_ref = ActorRef(
        actor=ExecutionActor(
            order_manager_ref=order_manager_ref,
            execution_adapter=SimulatedExecutionAdapter(BacktestCostModel()),
        ),
        mailbox=execution_mailbox,
    )
    instrument_context = BacktestInstrumentContext(
        registry_bars=(bar,),
    )
    projector = BacktestPortfolioProjector()
    processor = TargetIntentProcessor(
        risk_engine=RiskEngine([]),
        instrument_context=instrument_context,
        multiplier_for=projector.multiplier_for,
        broker_id=BrokerId("simulated"),
    )
    return (
        processor,
        order_manager_actor,
        order_manager_ref,
        execution_ref,
        account_actor,
        account_ref,
    )


def test_intent_processor_translates_quantity_intent_into_expected_order() -> None:
    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    processor, order_manager_actor, order_manager_ref, execution_ref, _, account_ref = (
        _new_environment(bar=bar)
    )
    result = processor.process_intent(
        TargetIntent(intent_type=TargetIntentType.QUANTITY, asset=_asset(), value=Decimal("3")),
        bar=bar,
        account_ref=account_ref,
        order_manager_ref=order_manager_ref,
        execution_ref=execution_ref,
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
        correlation_id=CorrelationId("corr-001"),
        order_number=1,
    )

    assert len(result.orders) == 1
    assert result.orders[0].intent.quantity == Decimal("3")
    assert result.orders[0].intent.account_id == AccountId("acct-backtest")
    assert result.fills
    assert result.fills[0].quantity == Decimal("3")


def test_intent_processor_translates_value_intent_into_expected_quantity() -> None:
    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), close="25")
    processor, order_manager_actor, order_manager_ref, execution_ref, _, account_ref = (
        _new_environment(bar=bar)
    )

    result = processor.process_intent(
        TargetIntent(intent_type=TargetIntentType.VALUE, asset=_asset(), value=Decimal("100")),
        bar=bar,
        account_ref=account_ref,
        order_manager_ref=order_manager_ref,
        execution_ref=execution_ref,
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
        correlation_id=CorrelationId("corr-002"),
        order_number=1,
    )

    assert result.orders[0].intent.quantity == Decimal("4")


def test_intent_processor_percent_target_uses_account_equity() -> None:
    """PERCENT intent targets a fraction of account equity, not max(current, price).

    Account starts with cash=10000. After buying 1 share at 100, equity = 10000.
    target_percent(0.2) → desired = 10000 * 0.2 / 100 = 20 shares.
    Already hold 1 → delta = 19 → buy 19.
    """
    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), close="100")
    processor, order_manager_actor, order_manager_ref, execution_ref, _, account_ref = (
        _new_environment(bar=bar)
    )

    first = processor.process_intent(
        TargetIntent(intent_type=TargetIntentType.QUANTITY, asset=_asset(), value=Decimal("1")),
        bar=bar,
        account_ref=account_ref,
        order_manager_ref=order_manager_ref,
        execution_ref=execution_ref,
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
        correlation_id=CorrelationId("corr-003"),
        order_number=1,
    )
    assert first.orders

    second_bar = _bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC), close="100")
    second = processor.process_intent(
        TargetIntent(intent_type=TargetIntentType.PERCENT, asset=_asset(), value=Decimal("0.2")),
        bar=second_bar,
        account_ref=account_ref,
        order_manager_ref=order_manager_ref,
        execution_ref=execution_ref,
        account_id=AccountId("acct-backtest"),
        strategy_id=StrategyId("strategy-backtest"),
        correlation_id=CorrelationId("corr-004"),
        order_number=2,
    )

    assert second.orders[0].intent.quantity == Decimal("19")
    assert second.orders[0].intent.side.value == "buy"


def test_intent_processor_rejects_missing_account_id() -> None:
    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    processor, order_manager_actor, order_manager_ref, execution_ref, _, account_ref = (
        _new_environment(bar=bar)
    )

    with pytest.raises(ValueError, match="account_id is required"):
        processor.process_intent(
            TargetIntent(
                intent_type=TargetIntentType.QUANTITY,
                asset=_asset(),
                value=Decimal("3"),
            ),
            bar=bar,
            account_ref=account_ref,
            order_manager_ref=order_manager_ref,
            execution_ref=execution_ref,
            account_id=None,
            strategy_id=StrategyId("strategy-backtest"),
            correlation_id=CorrelationId("corr-missing-account"),
            order_number=1,
        )
