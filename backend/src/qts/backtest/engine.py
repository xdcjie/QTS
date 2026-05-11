"""Backtest engine."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, tzinfo
from decimal import Decimal
from typing import Any

from qts.backtest.config import BacktestRunConfig
from qts.backtest.events import BacktestMarketDataEvent, order_backtest_events
from qts.backtest.historical_data_portal import HistoricalDataPortal
from qts.backtest.metrics import compute_equity_metrics
from qts.backtest.replay_clock import ReplayClock
from qts.backtest.report import BacktestReport, EquityCurvePoint, TradeLedgerEntry
from qts.core.ids import BacktestRunId, InstrumentId, OrderId
from qts.data.historical.chains import load_historical_chain
from qts.data.historical.config import HistoricalDataConfig
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
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.market_data_actor import MarketDataActor, MarketDataEvent
from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
from qts.runtime.actors.signal_aggregator_actor import (
    AggregatedSignalBatch,
    SignalAggregatorActor,
    StrategySignalEvent,
)
from qts.runtime.actors.strategy_actor import (
    StrategyActor,
    StrategyBarEvent,
    StrategyBarResult,
    StrategyFinalize,
    StrategyFinalized,
)
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


class BacktestEngine:
    """Single-process backtest engine using the Strategy SDK and actor order flow."""

    @dataclass(frozen=True, slots=True)
    class _ProcessedIntent:
        orders: tuple[Order, ...]
        fills: tuple[OrderFill, ...]

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
        future_roll_registry: FutureRollRegistry | None = None,
        warmup_bars: int = 0,
        target_timeframe: str | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
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
        self._future_roll_registry = future_roll_registry
        self._warmup_bars = warmup_bars
        self._target_timeframe = target_timeframe
        self._exchange_timezone_by_instrument = dict(exchange_timezone_by_instrument or {})
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
        future_roll_registry: FutureRollRegistry | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
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
            contract_multipliers=cls._contract_multipliers_from_config(config),
            future_roll_registry=future_roll_registry,
            warmup_bars=config.warmup_bars,
            target_timeframe=config.timeframe,
            exchange_timezone_by_instrument=exchange_timezone_by_instrument,
        )

    @staticmethod
    def _take_strategy_bar_result(mailbox: Mailbox) -> StrategyBarResult:
        if mailbox.empty():
            raise RuntimeError("strategy actor did not emit a bar result")
        result = mailbox.get()
        if not isinstance(result, StrategyBarResult):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one bar result")
        return result

    @staticmethod
    def _take_signal_batch(mailbox: Mailbox) -> AggregatedSignalBatch:
        if mailbox.empty():
            raise RuntimeError("signal aggregator actor did not emit a batch")
        result = mailbox.get()
        if not isinstance(result, AggregatedSignalBatch):
            raise TypeError(f"unexpected signal aggregator result: {type(result).__name__}")
        if not mailbox.empty():
            raise RuntimeError("signal aggregator actor emitted more than one batch")
        return result

    @staticmethod
    def _take_strategy_finalized(mailbox: Mailbox) -> StrategyFinalized:
        if mailbox.empty():
            raise RuntimeError("strategy actor did not emit finalization result")
        result = mailbox.get()
        if not isinstance(result, StrategyFinalized):
            raise TypeError(f"unexpected strategy actor result: {type(result).__name__}")
        if not mailbox.empty():
            raise RuntimeError("strategy actor emitted more than one finalization result")
        return result

    def _market_data_ref_for(
        self,
        bar: Bar,
        *,
        refs: dict[tuple[str | None, str | tzinfo | None], ActorRef],
        subscriber: ActorRef,
    ) -> ActorRef:
        aggregate_timeframe = None
        exchange_timezone: str | tzinfo | None = None
        if self._target_timeframe is not None and bar.timeframe != self._target_timeframe:
            aggregate_timeframe = self._target_timeframe
            try:
                exchange_timezone = self._exchange_timezone_by_instrument[bar.instrument_id]
            except KeyError as exc:
                raise RuntimeError(
                    f"exchange timezone is required to aggregate {bar.instrument_id} "
                    f"from {bar.timeframe} to {self._target_timeframe}"
                ) from exc
        key = (aggregate_timeframe, exchange_timezone)
        ref = refs.get(key)
        if ref is None:
            ref = ActorRef(
                actor=MarketDataActor(
                    subscribers=(subscriber,),
                    aggregate_timeframe=aggregate_timeframe,
                    exchange_timezone=exchange_timezone,
                ),
                mailbox=Mailbox(),
            )
            refs[key] = ref
        return ref

    def run(self) -> BacktestResult:
        instrument_registry = self._instrument_registry_for()

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

        ctx = StrategyContext(
            instrument_registry=instrument_registry,
            future_chain_registry=self._future_roll_registry,
        )
        strategy_result_mailbox = Mailbox()
        strategy_ref = ActorRef(
            actor=StrategyActor(
                strategy=self._strategy,
                context=ctx,
                result_ref=ActorRef(mailbox=strategy_result_mailbox),
            ),
            mailbox=Mailbox(),
        )
        signal_result_mailbox = Mailbox()
        signal_ref = ActorRef(
            actor=SignalAggregatorActor(result_ref=ActorRef(mailbox=signal_result_mailbox)),
            mailbox=Mailbox(),
        )

        orders: list[Order] = []
        fills: list[OrderFill] = []
        trade_ledger: list[TradeLedgerEntry] = []
        equity_curve: list[EquityCurvePoint] = []
        latest_prices: dict[InstrumentId, Decimal] = {}
        warmup_processed = 0
        trading_processed = 0

        strategy_bars_by_instrument: dict[InstrumentId, list[Bar]] = defaultdict(list)
        market_data_mailbox = Mailbox()
        market_data_subscriber = ActorRef(mailbox=market_data_mailbox)
        market_data_refs: dict[tuple[str | None, str | tzinfo | None], ActorRef] = {}
        events_by_time: dict[datetime, list[BacktestMarketDataEvent]] = defaultdict(list)
        for event in self._events:
            events_by_time[event.bar.end_time].append(event)
        replay_clock = ReplayClock(events_by_time.keys())
        event_index = 0
        while True:
            replay_time = replay_clock.advance()
            if replay_time is None:
                break
            for event in events_by_time[replay_time]:
                source_bar = event.bar
                market_data_ref = self._market_data_ref_for(
                    source_bar,
                    refs=market_data_refs,
                    subscriber=market_data_subscriber,
                )
                market_data_ref.tell(MarketDataEvent(payload=source_bar))
                market_data_ref.process_all()
                while not market_data_mailbox.empty():
                    payload = market_data_mailbox.get()
                    if not isinstance(payload, Bar):
                        raise TypeError(f"unexpected market data payload: {type(payload).__name__}")
                    bar = payload
                    strategy_bars_by_instrument[bar.instrument_id].append(bar)
                    portal = HistoricalDataPortal(strategy_bars_by_instrument)
                    latest_prices[bar.instrument_id] = bar.close
                    self._update_rolling_prices(
                        bar,
                        latest_prices=latest_prices,
                    )
                    strategy_ref.tell(
                        StrategyBarEvent(
                            bar=bar,
                            data=portal.data_view(as_of=bar.end_time),
                            portfolio=self._portfolio_view(
                                account_actor.snapshot(),
                                latest_prices=latest_prices,
                            ),
                        )
                    )
                    strategy_ref.process_all()
                    strategy_result = self._take_strategy_bar_result(strategy_result_mailbox)
                    if event_index < self._warmup_bars:
                        warmup_processed += 1
                        equity_curve.append(
                            self._equity_point(
                                bar,
                                account_actor.snapshot(),
                                latest_prices=latest_prices,
                            )
                        )
                        event_index += 1
                        continue

                    signal_ref.tell(
                        StrategySignalEvent(
                            bar=bar,
                            intents=strategy_result.intents,
                        )
                    )
                    signal_ref.process_all()
                    signal_batch = self._take_signal_batch(signal_result_mailbox)
                    for intent in signal_batch.intents:
                        processed = self._process_intent(
                            intent,
                            bar=bar,
                            account_actor=account_actor,
                            order_manager_actor=order_manager_actor,
                            order_manager_ref=order_manager_ref,
                            execution_ref=execution_ref,
                            account_ref=account_ref,
                            order_number=len(orders) + 1,
                        )
                        orders.extend(processed.orders)
                        fills.extend(processed.fills)
                        trade_ledger.extend(self._ledger_rows(processed.fills, bar=bar))
                    trading_processed += 1
                    equity_curve.append(
                        self._equity_point(
                            bar,
                            account_actor.snapshot(),
                            latest_prices=latest_prices,
                        )
                    )
                    event_index += 1

        strategy_ref.tell(StrategyFinalize())
        strategy_ref.process_all()
        _ = self._take_strategy_finalized(strategy_result_mailbox).intents

        if not equity_curve:
            equity_curve.append(
                EquityCurvePoint(
                    time=self._bars[-1].end_time if self._bars else self._zero_time(),
                    equity=self._initial_cash,
                )
            )
        config_hash = self._stable_hash(self._config)
        processed_bar_count = warmup_processed + trading_processed
        run_hash = self._report_hash(
            processed_bars=processed_bar_count,
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
            dataset_metadata=tuple(self._dataset_payload(item) for item in self._dataset_metadata),
            cost_model=self._cost_model.to_payload(),
            processed_bars=processed_bar_count,
            warmup_bars=warmup_processed,
            trading_bars=trading_processed,
            orders=tuple(self._order_payload(order) for order in orders),
            fills=tuple(self._fill_payload(fill) for fill in fills),
            trade_ledger=tuple(trade_ledger),
            equity_curve=tuple(equity_curve),
            metrics=compute_equity_metrics([point.equity for point in equity_curve]),
        )
        return BacktestResult(
            processed_bars=processed_bar_count,
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

    def _process_intent(
        self,
        intent: TargetIntent,
        *,
        bar: Bar,
        account_actor: AccountActor,
        order_manager_actor: OrderManagerActor,
        order_manager_ref: ActorRef,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        order_number: int,
    ) -> BacktestEngine._ProcessedIntent:
        snapshot = account_actor.snapshot()
        target_instrument = self._order_instrument_for_intent(intent, bar=bar)
        order_requests: list[tuple[InstrumentId, Decimal, Decimal]] = []
        if self._future_roll_registry is not None and self._future_roll_registry.is_continuous(
            intent.asset.instrument_id
        ):
            for instrument_id in self._future_roll_registry.related_contracts(
                intent.asset.instrument_id
            ):
                if instrument_id == target_instrument:
                    continue
                quantity = snapshot.positions.get(
                    instrument_id,
                    Position(instrument_id=instrument_id, quantity=Decimal("0")),
                ).quantity
                if quantity != Decimal("0"):
                    order_requests.append(
                        (
                            instrument_id,
                            -quantity,
                            self._future_roll_registry.execution_price(
                                intent.asset.instrument_id,
                                instrument_id,
                                as_of=bar.end_time,
                            ),
                        )
                    )

        current_quantity = snapshot.positions.get(
            target_instrument,
            Position(instrument_id=target_instrument, quantity=Decimal("0")),
        ).quantity
        desired_quantity = self._desired_quantity(
            intent, current_quantity=current_quantity, bar=bar
        )
        quantity_delta = desired_quantity - current_quantity
        if quantity_delta != Decimal("0"):
            order_requests.append(
                (
                    target_instrument,
                    quantity_delta,
                    self._market_price_for_intent(
                        intent,
                        instrument_id=target_instrument,
                        bar=bar,
                    ),
                )
            )
        if not order_requests:
            return self._ProcessedIntent(orders=(), fills=())

        orders: list[Order] = []
        fills: list[OrderFill] = []
        for index, (instrument_id, delta, market_price) in enumerate(order_requests):
            processed = self._process_order_delta(
                instrument_id=instrument_id,
                quantity_delta=delta,
                market_price=market_price,
                order_time=bar.end_time,
                order_manager_actor=order_manager_actor,
                order_manager_ref=order_manager_ref,
                execution_ref=execution_ref,
                account_ref=account_ref,
                order_number=order_number + index,
                multiplier=self._multiplier_for(instrument_id),
            )
            orders.extend(processed.orders)
            fills.extend(processed.fills)
        return self._ProcessedIntent(orders=tuple(orders), fills=tuple(fills))

    def _process_order_delta(
        self,
        *,
        instrument_id: InstrumentId,
        quantity_delta: Decimal,
        market_price: Decimal,
        order_time: Any,
        order_manager_actor: OrderManagerActor,
        order_manager_ref: ActorRef,
        execution_ref: ActorRef,
        account_ref: ActorRef,
        order_number: int,
        multiplier: Decimal,
    ) -> BacktestEngine._ProcessedIntent:
        if quantity_delta == Decimal("0"):
            return self._ProcessedIntent(orders=(), fills=())

        side = OrderSide.BUY if quantity_delta > Decimal("0") else OrderSide.SELL
        quantity = abs(quantity_delta)
        risk_decision = self._risk_engine.check(
            OrderRiskRequest(
                instrument_id=instrument_id,
                quantity=quantity,
                price=market_price,
                multiplier=multiplier,
                order_time=order_time,
            )
        )
        if not risk_decision.approved:
            return self._ProcessedIntent(orders=(), fills=())

        before_fill_count = len(order_manager_actor.fills)
        order_id = OrderId(f"bt-{order_number:06d}")
        order_intent = OrderIntent(
            order_id=order_id,
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
        )
        order_manager_ref.tell(
            SubmitOrder(
                intent=order_intent,
                risk_decision=risk_decision,
                broker_order_id=f"sim-{order_number:06d}",
                market_price=market_price,
            )
        )
        order_manager_ref.process_all()
        execution_ref.process_all()
        order_manager_ref.process_all()
        account_ref.process_all()
        fills = order_manager_actor.fills[before_fill_count:]
        return self._ProcessedIntent(orders=(order_manager_actor.get_order(order_id),), fills=fills)

    def _order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        if self._future_roll_registry is not None and self._future_roll_registry.is_continuous(
            intent.asset.instrument_id
        ):
            return self._future_roll_registry.resolve_contract(
                intent.asset.instrument_id,
                as_of=bar.end_time,
            )
        return intent.asset.instrument_id

    def _market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        if self._future_roll_registry is not None and self._future_roll_registry.is_continuous(
            intent.asset.instrument_id
        ):
            return self._future_roll_registry.execution_price(
                intent.asset.instrument_id,
                instrument_id,
                as_of=bar.end_time,
            )
        return bar.close

    @staticmethod
    def _desired_quantity(
        intent: TargetIntent,
        *,
        current_quantity: Decimal,
        bar: Bar,
    ) -> Decimal:
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

    def _update_rolling_prices(
        self,
        bar: Bar,
        *,
        latest_prices: dict[InstrumentId, Decimal],
    ) -> None:
        if self._future_roll_registry is None or not self._future_roll_registry.is_continuous(
            bar.instrument_id
        ):
            return
        for instrument_id in self._future_roll_registry.related_contracts(bar.instrument_id):
            try:
                latest_prices[instrument_id] = self._future_roll_registry.execution_price(
                    bar.instrument_id,
                    instrument_id,
                    as_of=bar.end_time,
                )
            except KeyError:
                continue

    def _portfolio_view(
        self,
        snapshot: AccountSnapshot,
        *,
        latest_prices: Mapping[InstrumentId, Decimal],
    ) -> PortfolioView:
        positions = {
            instrument_id: PortfolioPosition(
                quantity=position.quantity,
                market_value=(
                    position.quantity
                    * latest_prices.get(instrument_id, Decimal("0"))
                    * self._multiplier_for(instrument_id)
                ),
            )
            for instrument_id, position in snapshot.positions.items()
        }
        cash = snapshot.cash["USD"]
        equity = cash + sum(
            (position.market_value for position in positions.values()), Decimal("0")
        )
        return PortfolioView(cash=cash, equity=equity, positions=positions)

    def _equity_point(
        self,
        bar: Bar,
        snapshot: AccountSnapshot,
        *,
        latest_prices: Mapping[InstrumentId, Decimal],
    ) -> EquityCurvePoint:
        return EquityCurvePoint(
            time=bar.end_time,
            equity=self._portfolio_view(
                snapshot,
                latest_prices=latest_prices,
            ).equity,
        )

    def _instrument_registry_for(self) -> InstrumentRegistry:
        registry = InstrumentRegistry()
        seen: set[InstrumentId] = set()
        for bar in self._bars:
            if bar.instrument_id in seen:
                continue
            seen.add(bar.instrument_id)
            symbol = self._symbol_for(bar.instrument_id)
            registry.register(
                symbol,
                Instrument(
                    instrument_id=bar.instrument_id,
                    asset_class=AssetClass.EQUITY,
                    exchange=self._exchange_for(bar.instrument_id),
                    currency="USD",
                    contract_spec=ContractSpec(
                        tick_size=Decimal("0.01"),
                        lot_size=Decimal("1"),
                        multiplier=self._multiplier_for(bar.instrument_id),
                        settlement=SettlementType.CASH,
                        calendar_id="BACKTEST",
                    ),
                ),
            )
        return registry

    @staticmethod
    def _contract_multipliers_from_config(config: BacktestRunConfig) -> dict[InstrumentId, Decimal]:
        multipliers: dict[InstrumentId, Decimal] = {}
        historical_data_config = (
            HistoricalDataConfig.from_yaml(config.market_data.config_path)
            if config.market_data.config_path is not None
            else None
        )
        for root in config.roots:
            if historical_data_config is not None:
                if config.market_data.catalog is None:
                    raise RuntimeError("market data catalog is not configured")
                chain_path = historical_data_config.resolve_dataset(
                    config.market_data.catalog,
                    root,
                ).chain_path
            elif config.dataset_root is not None:
                chain_path = config.dataset_root / "chains" / f"{root}.json"
            else:
                chain_path = None
            if chain_path is None:
                if config.instrument_ids:
                    continue
                raise FileNotFoundError(
                    f"required historical chain file is missing for root: {root}"
                )
            if not chain_path.exists():
                if config.instrument_ids:
                    continue
                raise FileNotFoundError(f"required historical chain file is missing: {chain_path}")
            chain = load_historical_chain(chain_path)
            for contract in chain.contracts:
                multipliers[chain.instrument_id_for_symbol(contract.symbol)] = contract.multiplier
        return multipliers

    def _multiplier_for(self, instrument_id: InstrumentId) -> Decimal:
        return self._contract_multipliers.get(instrument_id, Decimal("1"))

    @staticmethod
    def _symbol_for(instrument_id: InstrumentId) -> str:
        return instrument_id.value.rsplit(".", maxsplit=1)[-1]

    @staticmethod
    def _exchange_for(instrument_id: InstrumentId) -> str:
        parts = instrument_id.value.split(".")
        if len(parts) >= 2:
            return parts[1]
        return "BACKTEST"

    @staticmethod
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

    @staticmethod
    def _order_payload(order: Order) -> dict[str, Any]:
        return {
            "order_id": order.order_id.value,
            "instrument_id": order.intent.instrument_id.value,
            "side": order.intent.side.value,
            "quantity": str(order.intent.quantity),
            "state": order.state.value,
            "broker_order_id": order.broker_order_id,
        }

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _stable_hash(payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    @classmethod
    def _report_hash(
        cls,
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
        return cls._stable_hash(
            {
                "processed_bars": processed_bars,
                "final_cash": str(final_cash),
                "order_ids": order_ids,
                "strategy_version": strategy_version,
                "config_hash": config_hash,
                "datasets": [cls._dataset_payload(item) for item in dataset_metadata],
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

    @staticmethod
    def _zero_time() -> Any:
        from datetime import UTC, datetime

        return datetime(1970, 1, 1, tzinfo=UTC)


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


__all__ = ["BacktestCostModel", "BacktestEngine", "BacktestResult"]
