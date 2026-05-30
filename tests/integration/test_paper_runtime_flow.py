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
    OrderIntent,
    OrderSide,
)
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy, TargetIntent


def test_example_strategy_runs_through_paper_simulated_runtime_session() -> None:
    from qts.data.events import MarketDataSubscription
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

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
    source = FakeStreamingMarketDataAdapter(source_id="paper-simulated-ci")
    source.subscribe(
        MarketDataSubscription(
            subscription_id="aapl-1m",
            instrument_id=instrument_id,
            timeframe="1m",
        )
    )
    source_event = source.emit(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    execution = _FillingExecutionAdapter()
    account_id = AccountId("acct-paper-runtime-flow")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=execution,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("1000")},
                account_id=account_id,
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
        )
    )

    session.start()
    assert isinstance(source_event.payload, Bar)
    result = session.on_market_data(source_event.payload)

    assert source.subscription_count == 1
    assert [intent.side for intent in execution.seen] == [OrderSide.BUY]
    assert result.fills[0].fill_id == "live-000001-fill"
    assert result.account_snapshot is not None
    assert result.account_snapshot.positions[instrument_id].quantity == Decimal("1")


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
        _ = account_id, strategy_id, client_order_id, correlation_id
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

    def replace_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        new_quantity: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = order_id, new_quantity, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-replace",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
        )


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
