"""Behavioral backtest/paper parity anchor (DR-022 / plan Task 3.2).

The legacy anchor ``test_backtest_live_parity.py`` proves the shared actor chain
by ``inspect.getsource`` substring matching. This anchor proves it
*behaviorally*: the SAME ``StrategyContext`` target intent is run through the
backtest actor loop AND a paper ``RuntimeSession`` with byte-identical inputs
(same instrument, same single bar/price, same initial cash, same risk config),
then the resulting OrderIntent / RiskDecision / Fill / AccountSnapshot deltas
are compared field-by-field.

Domain fact / invariant (CLAUDE.md §6 parity):
    Backtest and paper are execution modes of one system and must share the
    core path Strategy SDK -> StrategyContext -> intent -> RiskEngine ->
    OrderManagerActor -> ExecutionActor -> AccountActor. Given identical inputs
    they must produce identical *meaningful* results (side, quantity, fill
    price, cash delta, position quantity). Only boundary adapters
    (execution/market-data/clock) may differ.

Correct owner / boundary:
    ``BacktestEngine`` (backtest adapter boundary) and ``RuntimeSession``
    (paper adapter boundary) both reduce to the shared actor chain. This test
    owns the cross-mode equivalence assertion; the per-mode mechanics stay in
    their own modules.

Forbidden shortcut:
    A backtest-only or paper-only business path that bypasses Risk,
    OrderManager, or AccountActor. The bypass guard below fails if a fill is
    not reflected as a FILLED order *and* an AccountActor cash/position
    mutation, which can only occur through SubmitOrder -> ExecutionActor ->
    OrderManager fill -> ApplyFill.

Required gates / verification:
    This anchor (behavioral) plus the existing static anchor.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderState,
)
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.dependencies import RuntimeSessionDependencies
from qts.runtime.session import RuntimeSession, RuntimeSessionResult
from qts.strategy_sdk import PortfolioPosition, PortfolioView, TargetIntent

from tests.support.backtest_streaming import CapturedBacktestStream, run_engine_streaming
from tests.support.parity_strategy import ParityTargetQuantityStrategy

# Identical inputs shared by both runtimes.
_SYMBOL = "AAPL"
_INSTRUMENT_ID = InstrumentId("EQUITY.US.NASDAQ.AAPL")
_TARGET_QUANTITY = Decimal("2")
_INITIAL_CASH = Decimal("10000")
_BAR_PRICE = Decimal("100")
_BAR_START = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
# max_notional must admit the intent (2 * 100 = 200) so both modes approve.
_MAX_NOTIONAL = Decimal("1000000")


def test_backtest_and_paper_produce_identical_meaningful_results() -> None:
    bar = _parity_bar()

    backtest = _run_backtest(bar)
    paper = _run_paper(bar)

    backtest_intent = _backtest_meaningful_order(backtest)
    paper_intent = _paper_meaningful_order(paper)

    # --- Same OrderIntent shape (side, quantity, instrument) ---
    assert backtest_intent == paper_intent
    assert backtest_intent == _MeaningfulOrder(
        side="buy",
        quantity=_TARGET_QUANTITY,
        instrument_id=_INSTRUMENT_ID.value,
    )

    # --- Same RiskDecision outcome (approved): an order was submitted at all ---
    assert backtest.orders, "backtest produced no approved order"
    assert paper.orders, "paper produced no approved order"

    # --- Same Fill (quantity, price) ---
    backtest_fill = _backtest_meaningful_fill(backtest)
    paper_fill = _paper_meaningful_fill(paper)
    assert backtest_fill == paper_fill
    assert backtest_fill == _MeaningfulFill(
        side="buy",
        quantity=_TARGET_QUANTITY,
        price=_BAR_PRICE,
    )

    # --- Same AccountSnapshot delta (cash delta + position quantity) ---
    expected_cash_delta = -(_TARGET_QUANTITY * _BAR_PRICE)  # buy 2 @ 100, multiplier 1
    backtest_account = backtest.result.final_account
    paper_account = paper.account_snapshot
    assert paper_account is not None

    backtest_cash_delta = backtest_account.cash["USD"] - _INITIAL_CASH
    paper_cash_delta = paper_account.cash["USD"] - _INITIAL_CASH
    assert backtest_cash_delta == paper_cash_delta == expected_cash_delta

    backtest_position = backtest_account.positions[_INSTRUMENT_ID].quantity
    paper_position = paper_account.positions[_INSTRUMENT_ID].quantity
    assert backtest_position == paper_position == _TARGET_QUANTITY


def test_fill_is_applied_only_through_the_actor_owned_path() -> None:
    """Bypass guard: a fill must surface as a FILLED order *and* an account delta.

    A FILLED order only exists when OrderManagerActor processed the broker
    report; a non-zero cash/position delta only exists when AccountActor
    applied ``ApplyFill``. Any future path that bypasses Risk, OrderManager, or
    AccountActor (e.g. mutating the account directly from the engine) would
    leave one of these unset and fail this test in both runtimes.
    """
    bar = _parity_bar()

    backtest = _run_backtest(bar)
    paper = _run_paper(bar)

    # Backtest: the orders artifact records the OrderManager-owned terminal state.
    backtest_states = {order["state"] for order in backtest.orders}
    assert backtest_states == {OrderState.FILLED.value}
    assert backtest.fills, "backtest fill not routed through OrderManager"
    assert backtest.result.final_account.positions[_INSTRUMENT_ID].quantity == _TARGET_QUANTITY
    assert backtest.result.final_account.cash["USD"] != _INITIAL_CASH

    # Paper: orders come from the OrderManager snapshot; account from AccountActor.
    paper_states = {order.state for order in paper.orders}
    assert paper_states == {OrderState.FILLED}
    assert paper.fills, "paper fill not routed through OrderManager"
    assert paper.account_snapshot is not None
    assert paper.account_snapshot.positions[_INSTRUMENT_ID].quantity == _TARGET_QUANTITY
    assert paper.account_snapshot.cash["USD"] != _INITIAL_CASH


# --- meaningful-field projections (robust to incidental id/timestamp drift) ---


@dataclass(frozen=True, slots=True)
class _MeaningfulOrder:
    side: str
    quantity: Decimal
    instrument_id: str


@dataclass(frozen=True, slots=True)
class _MeaningfulFill:
    side: str
    quantity: Decimal
    price: Decimal


def _backtest_meaningful_order(captured: CapturedBacktestStream) -> _MeaningfulOrder:
    order = captured.orders[0]
    return _MeaningfulOrder(
        side=order["side"],
        quantity=Decimal(order["quantity"]),
        instrument_id=order["instrument_id"],
    )


def _paper_meaningful_order(result: RuntimeSessionResult) -> _MeaningfulOrder:
    order = result.orders[0]
    return _MeaningfulOrder(
        side=order.intent.side.value,
        quantity=order.intent.quantity,
        instrument_id=order.intent.instrument_id.value,
    )


def _backtest_meaningful_fill(captured: CapturedBacktestStream) -> _MeaningfulFill:
    fill = captured.fills[0]
    return _MeaningfulFill(
        side=fill["side"],
        quantity=Decimal(fill["quantity"]),
        price=Decimal(fill["price"]),
    )


def _paper_meaningful_fill(result: RuntimeSessionResult) -> _MeaningfulFill:
    fill = result.fills[0]
    return _MeaningfulFill(
        side=fill.side.value,
        quantity=fill.quantity,
        price=fill.price,
    )


# --- runtime construction (identical inputs, boundary adapters differ) ---


def _run_backtest(bar: Bar) -> CapturedBacktestStream:
    import tempfile

    with tempfile.TemporaryDirectory() as output_dir:
        return run_engine_streaming(
            BacktestEngine(
                strategy=ParityTargetQuantityStrategy(symbol=_SYMBOL, quantity=_TARGET_QUANTITY),
                bars=[bar],
                initial_cash=_INITIAL_CASH,
                risk_engine=RiskEngine([MaxNotionalRule(max_notional=_MAX_NOTIONAL)]),
                instrument_registry=_parity_registry(),
            ),
            Path(output_dir) / "parity-backtest",
        )


def _run_paper(bar: Bar) -> RuntimeSessionResult:
    account_id = AccountId("acct-paper-parity")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=ParityTargetQuantityStrategy(symbol=_SYMBOL, quantity=_TARGET_QUANTITY),
            risk_engine=RiskEngine([MaxNotionalRule(max_notional=_MAX_NOTIONAL)]),
            instrument_context=_ParityInstrumentContext(),
            execution_adapter=_FillingExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": _INITIAL_CASH},
                account_id=account_id,
            ),
            instrument_registry=_parity_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            order_submission_enabled=True,
            account_id=account_id,
        )
    )
    session.start()
    return session.on_market_data(bar)


def _parity_registry() -> InstrumentRegistry:
    registry = InstrumentRegistry()
    registry.register(
        _SYMBOL,
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
    return registry


def _parity_bar() -> Bar:
    # Flat bar (open == high == low == close) so both fill-timing policies and
    # both modes realize the decision at the same price.
    return Bar(
        instrument_id=_INSTRUMENT_ID,
        start_time=_BAR_START,
        end_time=_BAR_START + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=_BAR_PRICE,
        high=_BAR_PRICE,
        low=_BAR_PRICE,
        close=_BAR_PRICE,
        volume=Decimal("100"),
        is_complete=True,
    )


class _ParityInstrumentContext:
    """Minimal paper-side instrument context mirroring backtest resolution."""

    def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        del bar
        return intent.asset.instrument_id

    def market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        del intent, instrument_id
        return bar.close

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        del instrument_id
        return False

    def related_contracts_for(
        self,
        continuous_instrument_id: InstrumentId,
    ) -> frozenset[InstrumentId]:
        raise RuntimeError("continuous contracts are not configured")


@dataclass(slots=True)
class _FillingExecutionAdapter:
    """Paper execution boundary adapter: fills at the supplied market price."""

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
        del account_id, strategy_id, client_order_id, correlation_id, bar_time
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
        del order_id, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
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
