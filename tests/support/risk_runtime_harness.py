"""Reusable runtime harness for risk-rule integration tests.

Drives the shared runtime intent path (``TargetIntentProcessor`` ->
``RiskEngine`` -> ``OrderManagerActor`` -> ``ExecutionActor`` ->
``AccountActor``) used identically by backtest and paper runtimes, so a risk
rule's runtime enforcement can be exercised end-to-end without a full session.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.backtest.engine import BacktestCostModel
from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.core.ids import AccountId, BrokerId, CorrelationId, InstrumentId, StrategyId
from qts.domain.market_data import Bar
from qts.domain.risk import MarketDataRiskContext
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.risk.intraday_pnl import IntradayPnlCalculator
from qts.risk.margin.calculator import MarginCalculator
from qts.risk.risk_engine import RiskEngine
from qts.risk.rule import RiskRule
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor
from qts.runtime.intent_processing import ProcessedIntent, TargetIntentProcessor
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import TargetIntent, TargetIntentType
from qts.strategy_sdk.asset_ref import AssetRef

_DEFAULT_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def make_bar(
    when: datetime,
    close: str,
    instrument: InstrumentId = _DEFAULT_INSTRUMENT,
    *,
    session_id: str | None = None,
) -> Bar:
    """Build a complete one-minute bar at the supplied close.

    ``session_id`` defaults to the bar's UTC date (adequate for instruments
    whose session does not cross UTC midnight). Overnight-session tests pass
    an explicit exchange-local ``session_id`` that two bars on different UTC
    dates can share.
    """
    return Bar(
        instrument_id=instrument,
        start_time=when,
        end_time=when + timedelta(minutes=1),
        timeframe="1m",
        session_id=session_id if session_id is not None else when.date().isoformat(),
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


class RiskRuntimeHarness:
    """Construct and drive the shared runtime intent path for one account."""

    def __init__(
        self,
        *,
        rules: Sequence[RiskRule],
        multiplier: Decimal = Decimal("1"),
        initial_cash: Decimal = Decimal("100000"),
        margin_calculator: MarginCalculator | None = None,
        intraday_pnl_calculator: IntradayPnlCalculator | None = None,
        instrument: InstrumentId = _DEFAULT_INSTRUMENT,
    ) -> None:
        """Wire actors, execution, and the intent processor for the test."""
        self.instrument = instrument
        self._multiplier = multiplier
        self.account_actor = AccountActor(initial_cash={"USD": initial_cash})
        self.account_ref = ActorRef(actor=self.account_actor, mailbox=Mailbox())
        execution_mailbox = Mailbox()
        self.order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=execution_mailbox),
            account_ref=self.account_ref,
        )
        self.order_manager_ref = ActorRef(actor=self.order_manager_actor, mailbox=Mailbox())
        self.execution_ref = ActorRef(
            actor=ExecutionActor(
                order_manager_ref=self.order_manager_ref,
                execution_adapter=SimulatedExecutionAdapter(BacktestCostModel()),
            ),
            mailbox=execution_mailbox,
        )
        seed_bar = make_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC), "100", instrument)
        instrument_context = BacktestInstrumentContext(
            registry_bars=(seed_bar,),
            contract_multipliers={instrument: multiplier},
        )
        self.processor = TargetIntentProcessor(
            risk_engine=RiskEngine(list(rules)),
            instrument_context=instrument_context,
            multiplier_for=lambda _iid: multiplier,
            broker_id=BrokerId("simulated"),
            margin_calculator=margin_calculator,
            intraday_pnl_calculator=intraday_pnl_calculator,
        )
        self._order_number = 0

    def submit(
        self,
        *,
        target_quantity: str,
        when: datetime,
        price: str,
        intent_type: TargetIntentType = TargetIntentType.QUANTITY,
        market_data: MarketDataRiskContext | None = None,
        session_id: str | None = None,
    ) -> ProcessedIntent:
        """Submit one target intent at ``price`` and return the processed result.

        ``session_id`` overrides the bar's exchange-local session key, letting
        overnight-session tests place two bars on different UTC dates in the
        same trading session.
        """
        self._order_number += 1
        bar = make_bar(when, price, self.instrument, session_id=session_id)
        return self.processor.process_intent(
            TargetIntent(
                intent_type=intent_type,
                asset=AssetRef(instrument_id=self.instrument, symbol="AAPL"),
                value=Decimal(target_quantity),
            ),
            bar=bar,
            account_ref=self.account_ref,
            order_manager_ref=self.order_manager_ref,
            execution_ref=self.execution_ref,
            account_id=AccountId("acct-risk-harness"),
            strategy_id=StrategyId("strategy-risk-harness"),
            correlation_id=CorrelationId(f"corr-{self._order_number:03d}"),
            market_data_context=market_data,
            order_number=self._order_number,
        )


__all__ = ["RiskRuntimeHarness", "make_bar"]
