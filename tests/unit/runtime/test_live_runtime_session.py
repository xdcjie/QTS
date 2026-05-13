from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import InstrumentId, OrderId
from qts.domain.market_data import Bar
from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus, OrderIntent
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventSink
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy, TargetIntent


def _bar(start: datetime) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
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


class _BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.placed:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.placed = True


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
class _RecordingExecutionAdapter:
    seen: list[OrderIntent] = field(default_factory=list)

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        self.seen.append(intent)
        return ExecutionReport(
            report_id=f"{broker_order_id}-accepted",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
        )

    def cancel_order(self, order_id: OrderId, *, broker_order_id: str) -> ExecutionReport:
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


@dataclass(slots=True)
class _RecordingSink(RuntimeEventSink):
    events: list[RuntimeEvent] = field(default_factory=list)

    def write(self, event: RuntimeEvent) -> None:
        self.events.append(event)


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


def _registry() -> Any:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=instrument_id,
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
    return registry


def test_live_runtime_session_submits_only_through_actor_execution_path() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live import LiveRuntimeState
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("100000"))]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
        )
    )

    assert session.start() is LiveRuntimeState.RUNNING
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert len(adapter.seen) == 1
    assert result.orders[0].broker_order_id == "live-000001"
    assert result.account_snapshot is not None
    assert result.account_snapshot.positions == {}
    assert [event.kind for event in sink.events] == [
        "runtime.state_transition",
        "runtime.market_data",
        "runtime.strategy_intent",
        "runtime.order_submitted",
        "runtime.broker_report",
        "runtime.account_snapshot",
    ]


def test_live_runtime_session_blocks_intents_when_paused_or_degraded() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
        )
    )

    session.start()
    session.pause()
    paused = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    session.resume()
    session.degrade()
    degraded = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))

    assert adapter.seen == []
    assert paused.reason_code == "RUNTIME_PAUSED"
    assert degraded.reason_code == "RUNTIME_DEGRADED"


def test_live_runtime_session_observation_mode_keeps_market_data_without_orders() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            order_submission_enabled=False,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert adapter.seen == []
    assert result.reason_code == "ORDER_SUBMISSION_DISABLED"
    assert result.market_data[0].instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
