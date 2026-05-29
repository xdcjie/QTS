"""Integration: RuntimeSession actor supervision restart/degrade + idempotency.

Covers DR-017 / plan Task 9.1:

* A recoverable actor failure routed through the session supervisor yields a
  RESTART decision, emits a ``runtime.actor_failure`` event, and the session
  keeps running (continues to accept work).
* A non-recoverable actor failure degrades the session so it stops accepting
  new work while observability stays alive.
* An in-flight order cycle is idempotent under retry: re-delivering the same
  fill (as would happen when a recoverable failure replays a message) does not
  double-apply to account state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.market_data import Bar
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderFill,
    OrderIntent,
    OrderSide,
)
from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_path import ActorPath
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actor_supervisor import SupervisorDecision
from qts.runtime.mailbox import Mailbox
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventSink
from qts.runtime.state import RuntimeSessionState
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy, TargetIntent

_INSTRUMENT_ID = InstrumentId("EQUITY.US.NASDAQ.AAPL")
_ACCOUNT_ID = AccountId("acct-actor-failure-recovery")


def _build_session(sink: RuntimeEventSink) -> Any:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=_INSTRUMENT_ID,
            asset_class=AssetClass.EQUITY,
            exchange="NASDAQ",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.01"),
                lot_size=Decimal("1"),
                multiplier=Decimal("1"),
                settlement=SettlementType.CASH,
                calendar_id="NASDAQ",
            ),
        ),
    )
    return RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_FillingExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("1000")},
                account_id=_ACCOUNT_ID,
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=_ACCOUNT_ID,
            sink=sink,
        )
    )


def test_recoverable_actor_failure_restarts_and_session_continues() -> None:
    sink = _RecordingSink()
    session = _build_session(sink)
    session.start()
    state_before: RuntimeSessionState = session.state
    assert state_before is RuntimeSessionState.RUNNING

    # Route a recoverable failure through the session supervisor.
    event = ActorFailureEvent.from_exception(
        actor_name="/account",
        exception=ValueError("transient processing error"),
    )
    decision = session.on_actor_failure(event)

    assert decision is SupervisorDecision.RESTART
    # Session keeps running and still accepts work after a recoverable restart.
    state_after: RuntimeSessionState = session.state
    assert state_after is RuntimeSessionState.RUNNING
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    assert result.fills, "session should continue processing after a recoverable restart"

    failure_events = [e for e in sink.events if e.kind == "runtime.actor_failure"]
    assert len(failure_events) == 1
    assert failure_events[0].payload["decision"] == "RESTART"
    assert failure_events[0].payload["actor_name"] == "/account"


def test_non_recoverable_actor_failure_degrades_session() -> None:
    sink = _RecordingSink()
    session = _build_session(sink)
    session.start()
    state_before: RuntimeSessionState = session.state
    assert state_before is RuntimeSessionState.RUNNING

    event = ActorFailureEvent.from_exception(
        actor_name="/execution",
        exception=RuntimeError("broker connection lost permanently"),
        recoverable=False,
    )
    decision = session.on_actor_failure(event)

    assert decision is SupervisorDecision.DEGRADE
    # Non-recoverable failure degrades the session (stops accepting new work).
    state_after: RuntimeSessionState = session.state
    assert state_after is RuntimeSessionState.DEGRADED
    failure_events = [e for e in sink.events if e.kind == "runtime.actor_failure"]
    assert failure_events[-1].payload["decision"] == "DEGRADE"


def test_in_flight_order_cycle_is_idempotent_under_retry() -> None:
    """Re-delivering the same fill (retry after restart) must not double-apply."""
    from qts.runtime.actors.account_actor import AccountActor, ApplyFill

    actor = AccountActor(
        initial_cash={"USD": Decimal("1000")},
        account_id=_ACCOUNT_ID,
    )
    fill = OrderFill(
        fill_id="fill-cycle-001",
        order_id=OrderId("ord-cycle-001"),
        instrument_id=_INSTRUMENT_ID,
        side=OrderSide.BUY,
        quantity=Decimal("3"),
        price=Decimal("100"),
        account_id=_ACCOUNT_ID,
    )
    message = ApplyFill(fill=fill, currency="USD", multiplier=Decimal("1"))

    ref = ActorRef(actor=actor, mailbox=Mailbox(), path=ActorPath.root("account"))

    # First delivery applies the fill.
    ref.tell(message)
    ref.process_all()
    snapshot_after_first = actor.snapshot()
    assert snapshot_after_first.positions[_INSTRUMENT_ID].quantity == Decimal("3")
    assert snapshot_after_first.cash["USD"] == Decimal("700")

    # Retry the SAME fill (same fill_id) - simulates message replay on restart.
    ref.tell(message)
    ref.process_all()
    snapshot_after_retry = actor.snapshot()

    # Idempotent: position and cash are unchanged by the retry.
    assert snapshot_after_retry.positions[_INSTRUMENT_ID].quantity == Decimal("3")
    assert snapshot_after_retry.cash["USD"] == Decimal("700")
    assert snapshot_after_retry.seen_fill_ids == ("fill-cycle-001",)


class _RecordingSink(RuntimeEventSink):
    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []

    def write(self, event: RuntimeEvent) -> object:
        self.events.append(event)
        return None


class _BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.done = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.done:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.done = True


class _InstrumentContext:
    def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        return intent.asset.instrument_id

    def market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        return bar.close

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        return False

    def related_contracts_for(
        self,
        continuous_instrument_id: InstrumentId,
    ) -> frozenset[InstrumentId]:
        raise RuntimeError("continuous contracts are not configured")


@dataclass(slots=True)
class _FillingExecutionAdapter:
    seen: list[OrderIntent] = field(default_factory=list)

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
        bar_time: object | None = None,
    ) -> ExecutionReport:
        _ = account_id, strategy_id, client_order_id, correlation_id, bar_time
        self.seen.append(intent)
        return ExecutionReport(
            report_id=f"{broker_order_id}-filled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill",
        )

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = order_id, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


def _bar(start: datetime) -> Bar:
    return Bar(
        instrument_id=_INSTRUMENT_ID,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


def _portfolio_view(
    snapshot: Any,
    *,
    latest_prices: Mapping[InstrumentId, Decimal],
) -> PortfolioView:
    positions = {
        instrument_id: PortfolioPosition(
            quantity=position.quantity,
            market_value=position.quantity * latest_prices.get(instrument_id, Decimal("0")),
        )
        for instrument_id, position in snapshot.positions.items()
    }
    cash = snapshot.cash["USD"]
    return PortfolioView(
        cash=cash,
        equity=cash + sum((position.market_value for position in positions.values()), Decimal("0")),
        positions=positions,
    )
