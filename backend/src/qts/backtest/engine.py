"""Backtest engine."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from qts.backtest.config import BacktestRunConfig
from qts.backtest.events import BacktestMarketDataEvent, order_backtest_events
from qts.backtest.historical_data_portal import HistoricalDataPortal
from qts.backtest.metrics import compute_equity_metrics
from qts.backtest.report import BacktestReport, EquityCurvePoint, TradeLedgerEntry
from qts.core.ids import BacktestRunId, InstrumentId, OrderId
from qts.data.historical.chains import load_historical_chain
from qts.data.provenance import DatasetMetadata
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.domain.risk import OrderRiskRequest
from qts.execution.order_manager import (
    ExecutionReport,
    ExecutionReportStatus,
    Order,
    OrderFill,
    OrderIntent,
    OrderSide,
)
from qts.portfolio.position_book import Position
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import (
    PortfolioPosition,
    PortfolioView,
    Strategy,
    StrategyContext,
    TargetIntent,
)
from qts.strategy_sdk.target import TargetIntentType


@dataclass(frozen=True, slots=True)
class BacktestCostModel:
    """Explicit simulation cost assumptions included in reports."""

    fixed_commission_per_contract: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")
    latency_model: str = "zero"

    def __post_init__(self) -> None:
        if self.fixed_commission_per_contract < Decimal("0"):
            raise ValueError("fixed_commission_per_contract must be non-negative")
        if self.slippage_bps < Decimal("0"):
            raise ValueError("slippage_bps must be non-negative")
        if not self.latency_model.strip():
            raise ValueError("latency_model must not be empty")

    def to_payload(self) -> dict[str, str]:
        return {
            "fixed_commission_per_contract": str(self.fixed_commission_per_contract),
            "slippage_bps": str(self.slippage_bps),
            "latency_model": self.latency_model,
        }

    @property
    def slippage_model(self) -> str:
        return "zero" if self.slippage_bps == Decimal("0") else "basis_points"

    @property
    def commission_model(self) -> str:
        if self.fixed_commission_per_contract == Decimal("0"):
            return "zero"
        return "fixed_per_contract"


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Backtest run result."""

    processed_bars: int
    warmup_bars: int
    trading_bars: int
    final_account: AccountSnapshot
    orders: tuple[Order, ...]
    fills: tuple[OrderFill, ...]
    run_id: BacktestRunId
    strategy_version: str
    config_hash: str
    dataset_metadata: tuple[DatasetMetadata, ...]
    cost_model: BacktestCostModel
    report_hash: str
    report: BacktestReport


@dataclass(frozen=True, slots=True)
class _ProcessedIntent:
    order: Order | None
    fills: tuple[OrderFill, ...]


class BacktestEngine:
    """Single-process backtest engine using the Strategy SDK and actor order flow."""

    def __init__(
        self,
        *,
        strategy: Strategy,
        bars: Iterable[Bar],
        initial_cash: Decimal,
        risk_engine: RiskEngine | None = None,
        dataset_metadata: Iterable[DatasetMetadata] = (),
        config: dict[str, Any] | None = None,
        strategy_version: str | None = None,
        cost_model: BacktestCostModel | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
        warmup_bars: int = 0,
    ) -> None:
        self._strategy = strategy
        self._events = order_backtest_events(
            BacktestMarketDataEvent(bar=bar, source_sequence=index)
            for index, bar in enumerate(bars)
        )
        self._bars = tuple(event.bar for event in self._events)
        self._initial_cash = initial_cash
        self._dataset_metadata = tuple(dataset_metadata)
        self._config = config or {}
        self._strategy_version = strategy_version or strategy.__class__.__qualname__
        self._cost_model = cost_model or BacktestCostModel()
        self._contract_multipliers = dict(contract_multipliers or {})
        self._warmup_bars = warmup_bars
        self._risk_engine = risk_engine or RiskEngine(
            [MaxNotionalRule(max_notional=initial_cash * Decimal("100"))]
        )

    @classmethod
    def from_config(
        cls,
        config: BacktestRunConfig,
        *,
        bars: Iterable[Bar],
        strategy: Strategy,
        dataset_metadata: Iterable[DatasetMetadata] = (),
    ) -> BacktestEngine:
        cost_model = BacktestCostModel(
            fixed_commission_per_contract=config.cost_model.fixed_commission_per_contract,
            slippage_bps=config.cost_model.slippage_bps,
        )
        risk_engine = RiskEngine([MaxNotionalRule(max_notional=config.risk_config.max_notional)])
        return cls(
            strategy=strategy,
            bars=bars,
            initial_cash=config.initial_cash,
            risk_engine=risk_engine,
            dataset_metadata=dataset_metadata,
            config=config.to_payload(),
            strategy_version=config.strategy_class,
            cost_model=cost_model,
            contract_multipliers=_contract_multipliers_from_config(config),
            warmup_bars=config.warmup_bars,
        )

    def run(self) -> BacktestResult:
        bars_by_instrument: dict[InstrumentId, list[Bar]] = defaultdict(list)
        for bar in self._bars:
            bars_by_instrument[bar.instrument_id].append(bar)
        portal = HistoricalDataPortal(bars_by_instrument)
        instrument_registry = _instrument_registry_for(
            self._bars,
            contract_multipliers=self._contract_multipliers,
        )

        account_actor = AccountActor(initial_cash={"USD": self._initial_cash})
        account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
        execution_mailbox = Mailbox()
        order_manager_mailbox = Mailbox()
        order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=execution_mailbox),
            account_ref=account_ref,
            multiplier_by_instrument=self._contract_multipliers,
        )
        order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
        execution_ref = ActorRef(
            actor=ExecutionActor(
                order_manager_ref=order_manager_ref,
                execution_adapter=_BacktestExecutionAdapter(self._cost_model),
            ),
            mailbox=execution_mailbox,
        )

        ctx = StrategyContext(instrument_registry=instrument_registry)
        self._strategy.initialize(ctx)

        orders: list[Order] = []
        fills: list[OrderFill] = []
        trade_ledger: list[TradeLedgerEntry] = []
        equity_curve: list[EquityCurvePoint] = []
        latest_prices: dict[InstrumentId, Decimal] = {}
        warmup_processed = 0
        trading_processed = 0

        for event_index, event in enumerate(self._events):
            bar = event.bar
            latest_prices[bar.instrument_id] = bar.close
            ctx.data = portal.data_view(as_of=bar.end_time)
            ctx.portfolio = _portfolio_view(
                account_actor.snapshot(),
                latest_prices=latest_prices,
                multipliers=self._contract_multipliers,
            )
            ctx.indicator.update_from_bar(bar)
            before_count = len(ctx.intents)
            self._strategy.on_bar(ctx, bar)
            if event_index < self._warmup_bars:
                warmup_processed += 1
                equity_curve.append(
                    _equity_point(
                        bar,
                        account_actor.snapshot(),
                        latest_prices=latest_prices,
                        multipliers=self._contract_multipliers,
                    )
                )
                continue

            for intent in ctx.intents[before_count:]:
                processed = _process_intent(
                    intent,
                    bar=bar,
                    account_actor=account_actor,
                    order_manager_actor=order_manager_actor,
                    order_manager_ref=order_manager_ref,
                    execution_ref=execution_ref,
                    account_ref=account_ref,
                    risk_engine=self._risk_engine,
                    order_number=len(orders) + 1,
                    multiplier=_multiplier_for(
                        intent.asset.instrument_id,
                        self._contract_multipliers,
                    ),
                )
                if processed.order is not None:
                    orders.append(processed.order)
                fills.extend(processed.fills)
                trade_ledger.extend(_ledger_rows(processed.fills, bar=bar))
            trading_processed += 1
            equity_curve.append(
                _equity_point(
                    bar,
                    account_actor.snapshot(),
                    latest_prices=latest_prices,
                    multipliers=self._contract_multipliers,
                )
            )

        before_finalize_count = len(ctx.intents)
        finalize = getattr(self._strategy, "finalize", None)
        if finalize is not None:
            finalize(ctx)
        _ = ctx.intents[before_finalize_count:]

        if not equity_curve:
            equity_curve.append(
                EquityCurvePoint(
                    time=self._bars[-1].end_time if self._bars else _zero_time(),
                    equity=self._initial_cash,
                )
            )
        config_hash = _stable_hash(self._config)
        run_hash = _report_hash(
            processed_bars=len(self._events),
            final_cash=account_actor.snapshot().cash["USD"],
            order_ids=tuple(order.order_id.value for order in orders),
            strategy_version=self._strategy_version,
            config_hash=config_hash,
            dataset_metadata=self._dataset_metadata,
            cost_model=self._cost_model,
            trade_ledger=tuple(trade_ledger),
        )
        run_id = BacktestRunId(f"bt-{run_hash.removeprefix('sha256:')[:12]}")
        report = BacktestReport(
            run_id=run_id,
            config_hash=config_hash,
            dataset_metadata=tuple(_dataset_payload(item) for item in self._dataset_metadata),
            cost_model=self._cost_model.to_payload(),
            processed_bars=len(self._events),
            warmup_bars=warmup_processed,
            trading_bars=trading_processed,
            orders=tuple(_order_payload(order) for order in orders),
            fills=tuple(_fill_payload(fill) for fill in fills),
            trade_ledger=tuple(trade_ledger),
            equity_curve=tuple(equity_curve),
            metrics=compute_equity_metrics([point.equity for point in equity_curve]),
        )
        return BacktestResult(
            processed_bars=len(self._events),
            warmup_bars=warmup_processed,
            trading_bars=trading_processed,
            final_account=account_actor.snapshot(),
            orders=tuple(orders),
            fills=tuple(fills),
            run_id=run_id,
            strategy_version=self._strategy_version,
            config_hash=config_hash,
            dataset_metadata=self._dataset_metadata,
            cost_model=self._cost_model,
            report_hash=report.report_hash,
            report=report,
        )


class _BacktestExecutionAdapter:
    def __init__(self, cost_model: BacktestCostModel) -> None:
        self._cost_model = cost_model

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        slippage = market_price * self._cost_model.slippage_bps / Decimal("10000")
        fill_price = (
            market_price + slippage if intent.side is OrderSide.BUY else market_price - slippage
        )
        commission = self._cost_model.fixed_commission_per_contract * intent.quantity
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=fill_price,
            fill_id=f"{broker_order_id}-fill-1",
            commission=commission,
            slippage=abs(fill_price - market_price),
        )


def _process_intent(
    intent: TargetIntent,
    *,
    bar: Bar,
    account_actor: AccountActor,
    order_manager_actor: OrderManagerActor,
    order_manager_ref: ActorRef,
    execution_ref: ActorRef,
    account_ref: ActorRef,
    risk_engine: RiskEngine,
    order_number: int,
    multiplier: Decimal,
) -> _ProcessedIntent:
    current_quantity = (
        account_actor.snapshot()
        .positions.get(
            intent.asset.instrument_id,
            Position(instrument_id=intent.asset.instrument_id, quantity=Decimal("0")),
        )
        .quantity
    )
    desired_quantity = _desired_quantity(intent, current_quantity=current_quantity, bar=bar)
    quantity_delta = desired_quantity - current_quantity
    if quantity_delta == Decimal("0"):
        return _ProcessedIntent(order=None, fills=())

    side = OrderSide.BUY if quantity_delta > Decimal("0") else OrderSide.SELL
    quantity = abs(quantity_delta)
    risk_decision = risk_engine.check(
        OrderRiskRequest(
            instrument_id=intent.asset.instrument_id,
            quantity=quantity,
            price=bar.close,
            multiplier=multiplier,
            order_time=bar.end_time,
        )
    )
    if not risk_decision.approved:
        return _ProcessedIntent(order=None, fills=())

    before_fill_count = len(order_manager_actor.fills)
    order_id = OrderId(f"bt-{order_number:06d}")
    order_intent = OrderIntent(
        order_id=order_id,
        instrument_id=intent.asset.instrument_id,
        side=side,
        quantity=quantity,
    )
    order_manager_ref.tell(
        SubmitOrder(
            intent=order_intent,
            risk_decision=risk_decision,
            broker_order_id=f"sim-{order_number:06d}",
            market_price=bar.close,
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()
    fills = order_manager_actor.fills[before_fill_count:]
    return _ProcessedIntent(order=order_manager_actor.get_order(order_id), fills=fills)


def _desired_quantity(intent: TargetIntent, *, current_quantity: Decimal, bar: Bar) -> Decimal:
    if intent.intent_type is TargetIntentType.CLOSE:
        return Decimal("0")
    if intent.value is None:
        raise ValueError("target intent value is required")
    if intent.intent_type is TargetIntentType.QUANTITY:
        return intent.value
    if intent.intent_type is TargetIntentType.VALUE:
        return intent.value / bar.close
    if intent.intent_type is TargetIntentType.PERCENT:
        current_value = current_quantity * bar.close
        target_value = max(current_value, bar.close) * intent.value
        return target_value / bar.close
    raise ValueError(f"unsupported target intent type: {intent.intent_type}")


def _portfolio_view(
    snapshot: AccountSnapshot,
    *,
    latest_prices: Mapping[InstrumentId, Decimal],
    multipliers: Mapping[InstrumentId, Decimal],
) -> PortfolioView:
    positions = {
        instrument_id: PortfolioPosition(
            quantity=position.quantity,
            market_value=(
                position.quantity
                * latest_prices.get(instrument_id, Decimal("0"))
                * _multiplier_for(instrument_id, multipliers)
            ),
        )
        for instrument_id, position in snapshot.positions.items()
    }
    cash = snapshot.cash["USD"]
    equity = cash + sum((position.market_value for position in positions.values()), Decimal("0"))
    return PortfolioView(cash=cash, equity=equity, positions=positions)


def _equity_point(
    bar: Bar,
    snapshot: AccountSnapshot,
    *,
    latest_prices: Mapping[InstrumentId, Decimal],
    multipliers: Mapping[InstrumentId, Decimal],
) -> EquityCurvePoint:
    return EquityCurvePoint(
        time=bar.end_time,
        equity=_portfolio_view(
            snapshot,
            latest_prices=latest_prices,
            multipliers=multipliers,
        ).equity,
    )


def _instrument_registry_for(
    bars: Iterable[Bar],
    *,
    contract_multipliers: Mapping[InstrumentId, Decimal],
) -> InstrumentRegistry:
    registry = InstrumentRegistry()
    seen: set[InstrumentId] = set()
    for bar in bars:
        if bar.instrument_id in seen:
            continue
        seen.add(bar.instrument_id)
        symbol = _symbol_for(bar.instrument_id)
        registry.register(
            symbol,
            Instrument(
                instrument_id=bar.instrument_id,
                asset_class=AssetClass.EQUITY,
                exchange=_exchange_for(bar.instrument_id),
                currency="USD",
                contract_spec=ContractSpec(
                    tick_size=Decimal("0.01"),
                    lot_size=Decimal("1"),
                    multiplier=_multiplier_for(bar.instrument_id, contract_multipliers),
                    settlement=SettlementType.CASH,
                    calendar_id="BACKTEST",
                ),
            ),
        )
    return registry


def _contract_multipliers_from_config(config: BacktestRunConfig) -> dict[InstrumentId, Decimal]:
    multipliers: dict[InstrumentId, Decimal] = {}
    for root in config.roots:
        chain_path = config.dataset_root / "chains" / f"{root}.json"
        if not chain_path.exists():
            if config.instrument_ids:
                continue
            raise FileNotFoundError(f"required historical chain file is missing: {chain_path}")
        chain = load_historical_chain(chain_path)
        for contract in chain.contracts:
            multipliers[chain.instrument_id_for_symbol(contract.symbol)] = contract.multiplier
    return multipliers


def _multiplier_for(
    instrument_id: InstrumentId,
    multipliers: Mapping[InstrumentId, Decimal],
) -> Decimal:
    return multipliers.get(instrument_id, Decimal("1"))


def _symbol_for(instrument_id: InstrumentId) -> str:
    return instrument_id.value.rsplit(".", maxsplit=1)[-1]


def _exchange_for(instrument_id: InstrumentId) -> str:
    parts = instrument_id.value.split(".")
    if len(parts) >= 2:
        return parts[1]
    return "BACKTEST"


def _ledger_rows(fills: Iterable[OrderFill], *, bar: Bar) -> tuple[TradeLedgerEntry, ...]:
    return tuple(
        TradeLedgerEntry(
            order_id=fill.order_id.value,
            instrument_id=fill.instrument_id.value,
            side=fill.side.value,
            quantity=fill.quantity,
            fill_price=fill.price,
            commission=fill.commission,
            slippage=fill.slippage,
            fill_time=bar.end_time,
            source_bar_time=bar.start_time,
        )
        for fill in fills
    )


def _order_payload(order: Order) -> dict[str, Any]:
    return {
        "order_id": order.order_id.value,
        "instrument_id": order.intent.instrument_id.value,
        "side": order.intent.side.value,
        "quantity": str(order.intent.quantity),
        "state": order.state.value,
        "broker_order_id": order.broker_order_id,
    }


def _fill_payload(fill: OrderFill) -> dict[str, Any]:
    return {
        "fill_id": fill.fill_id,
        "order_id": fill.order_id.value,
        "instrument_id": fill.instrument_id.value,
        "side": fill.side.value,
        "quantity": str(fill.quantity),
        "price": str(fill.price),
        "commission": str(fill.commission),
        "slippage": str(fill.slippage),
    }


def _dataset_payload(item: DatasetMetadata) -> dict[str, Any]:
    return {
        "dataset_id": item.dataset_id,
        "source": item.source,
        "instrument_id": item.instrument_id.value,
        "timeframe": item.timeframe,
        "timezone_policy": item.timezone_policy,
        "adjustment_policy": item.adjustment_policy,
        "normalization_version": item.normalization_version,
        "created_at": item.created_at.isoformat(),
        "content_hash": item.content_hash,
    }


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _report_hash(
    *,
    processed_bars: int,
    final_cash: Decimal,
    order_ids: tuple[str, ...],
    strategy_version: str,
    config_hash: str,
    dataset_metadata: tuple[DatasetMetadata, ...],
    cost_model: BacktestCostModel,
    trade_ledger: tuple[TradeLedgerEntry, ...],
) -> str:
    return _stable_hash(
        {
            "processed_bars": processed_bars,
            "final_cash": str(final_cash),
            "order_ids": order_ids,
            "strategy_version": strategy_version,
            "config_hash": config_hash,
            "datasets": [_dataset_payload(item) for item in dataset_metadata],
            "cost_model": cost_model.to_payload(),
            "trade_ledger": [
                {
                    "order_id": row.order_id,
                    "instrument_id": row.instrument_id,
                    "side": row.side,
                    "quantity": str(row.quantity),
                    "fill_price": str(row.fill_price),
                    "commission": str(row.commission),
                    "slippage": str(row.slippage),
                    "fill_time": row.fill_time.isoformat(),
                    "source_bar_time": row.source_bar_time.isoformat(),
                }
                for row in trade_ledger
            ],
        }
    )


def _zero_time() -> Any:
    from datetime import UTC, datetime

    return datetime(1970, 1, 1, tzinfo=UTC)


__all__ = ["BacktestCostModel", "BacktestEngine", "BacktestResult"]
