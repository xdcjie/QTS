"""Backtest engine."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, tzinfo
from decimal import Decimal
from typing import Any

from qts.backtest.config import BacktestRunConfig
from qts.backtest.historical_data_portal import HistoricalDataPortal
from qts.backtest.report import (
    EquityCurvePoint,
    StreamingBacktestArtifactWriter,
    TradeLedgerEntry,
)
from qts.core.ids import BacktestRunId, InstrumentId, OrderId
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
class BacktestStreamResult:
    """Backtest result written to partitioned streaming artifacts."""

    processed_bars: int
    warmup_bars: int
    trading_bars: int
    final_account: AccountSnapshot
    run_id: BacktestRunId
    strategy_version: str
    config_hash: str
    dataset_metadata: tuple[DatasetMetadata, ...]
    cost_model: BacktestCostModel
    report_hash: str
    manifest_path: Any
    artifact_paths: dict[str, Any]
    artifact_rows: dict[str, int]
    artifact_hashes: dict[str, str]


class BacktestEngine:
    """Single-process backtest engine using the Strategy SDK and actor order flow."""

    @dataclass(frozen=True, slots=True)
    class _ProcessedIntent:
        orders: tuple[Order, ...]
        fills: tuple[OrderFill, ...]

    @dataclass(frozen=True, slots=True)
    class _RuntimeRunResult:
        final_account: AccountSnapshot
        warmup_bars: int
        trading_bars: int
        last_bar: Bar | None

        @property
        def processed_bars(self) -> int:
            return self.warmup_bars + self.trading_bars

    class _StreamingBacktestSink:
        def __init__(self, writer: StreamingBacktestArtifactWriter) -> None:
            self._writer = writer
            self._order_count = 0

        @property
        def order_count(self) -> int:
            return self._order_count

        def write_processed(
            self,
            engine: BacktestEngine,
            processed: BacktestEngine._ProcessedIntent,
            *,
            bar: Bar,
        ) -> None:
            for order in processed.orders:
                self._writer.write_order(engine._order_payload(order))
            for fill in processed.fills:
                self._writer.write_fill(engine._fill_payload(fill))
            for row in engine._ledger_rows(processed.fills, bar=bar):
                self._writer.write_trade_ledger(row)
            self._order_count += len(processed.orders)

        def write_equity_point(self, point: EquityCurvePoint) -> None:
            self._writer.write_equity_point(point)

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
        instrument_registry: InstrumentRegistry | None = None,
    ) -> None:
        self._strategy = strategy
        if instrument_registry is None and isinstance(bars, Sequence):
            self._registry_bars = tuple(bars)
            self._bars = iter(self._registry_bars)
        else:
            self._registry_bars = ()
            self._bars = iter(bars)
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
        self._instrument_registry = instrument_registry
        self._related_contracts_by_continuous: dict[InstrumentId, frozenset[InstrumentId]] = {}
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
        instrument_registry: InstrumentRegistry | None = None,
        dataset_metadata: Iterable[DatasetMetadata] = (),
        future_roll_registry: FutureRollRegistry | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
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
            contract_multipliers=contract_multipliers,
            future_roll_registry=future_roll_registry,
            warmup_bars=config.warmup_bars,
            target_timeframe=config.timeframe,
            exchange_timezone_by_instrument=exchange_timezone_by_instrument,
            instrument_registry=instrument_registry,
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

    def _run_actor_loop(
        self,
        *,
        sink: BacktestEngine._StreamingBacktestSink,
        prune_history: bool,
        compact_orders: bool,
    ) -> BacktestEngine._RuntimeRunResult:
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

        latest_prices: dict[InstrumentId, Decimal] = {}
        warmup_processed = 0
        trading_processed = 0
        event_index = 0
        last_bar: Bar | None = None
        history_limit = self._history_limit_from_subscriptions(ctx) if prune_history else None

        strategy_bars_by_instrument: dict[InstrumentId, list[Bar]] = defaultdict(list)
        market_data_mailbox = Mailbox()
        market_data_subscriber = ActorRef(mailbox=market_data_mailbox)
        market_data_refs: dict[tuple[str | None, str | tzinfo | None], ActorRef] = {}
        for source_bar in self._bars:
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
                last_bar = bar
                history = strategy_bars_by_instrument[bar.instrument_id]
                history.append(bar)
                if history_limit is not None and len(history) > history_limit:
                    del history[: len(history) - history_limit]
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
                    sink.write_equity_point(
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
                        order_number=sink.order_count + 1,
                    )
                    sink.write_processed(self, processed, bar=bar)
                    if compact_orders:
                        order_manager_actor.compact_for_streaming(
                            order.order_id for order in processed.orders
                        )
                trading_processed += 1
                sink.write_equity_point(
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
        return BacktestEngine._RuntimeRunResult(
            final_account=account_actor.snapshot(),
            warmup_bars=warmup_processed,
            trading_bars=trading_processed,
            last_bar=last_bar,
        )

    def run_streaming(self, output_dir: Any) -> BacktestStreamResult:
        writer = StreamingBacktestArtifactWriter(output_dir)
        sink = BacktestEngine._StreamingBacktestSink(writer)
        runtime = self._run_actor_loop(
            sink=sink,
            prune_history=True,
            compact_orders=True,
        )

        if runtime.processed_bars == 0:
            sink.write_equity_point(
                EquityCurvePoint(
                    time=runtime.last_bar.end_time
                    if runtime.last_bar is not None
                    else self._zero_time(),
                    equity=self._initial_cash,
                )
            )
        config_hash = self._stable_hash(self._config)
        processed_bar_count = runtime.processed_bars
        run_id_value, report_hash, _, artifacts = writer.finalize(
            config_hash=config_hash,
            dataset_metadata=tuple(self._dataset_payload(item) for item in self._dataset_metadata),
            cost_model=self._cost_model.to_payload(),
            processed_bars=processed_bar_count,
            warmup_bars=runtime.warmup_bars,
            trading_bars=runtime.trading_bars,
            final_cash=runtime.final_account.cash["USD"],
            strategy_version=self._strategy_version,
        )
        return BacktestStreamResult(
            processed_bars=processed_bar_count,
            warmup_bars=runtime.warmup_bars,
            trading_bars=runtime.trading_bars,
            final_account=runtime.final_account,
            run_id=BacktestRunId(run_id_value),
            strategy_version=self._strategy_version,
            config_hash=config_hash,
            dataset_metadata=self._dataset_metadata,
            cost_model=self._cost_model,
            report_hash=report_hash,
            manifest_path=artifacts.manifest_path,
            artifact_paths=artifacts.artifact_paths,
            artifact_rows=artifacts.artifact_rows,
            artifact_hashes=artifacts.artifact_hashes,
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
            related_contracts = self._related_contracts_for(intent.asset.instrument_id)
            for instrument_id, position in snapshot.positions.items():
                if instrument_id == target_instrument:
                    continue
                if instrument_id not in related_contracts:
                    continue
                quantity = position.quantity
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

        before_fill_count = order_manager_actor.fill_count
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
        fills = order_manager_actor.fills_since(before_fill_count)
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
        try:
            instrument_id = self._future_roll_registry.resolve_contract(
                bar.instrument_id,
                as_of=bar.end_time,
            )
            latest_prices[instrument_id] = self._future_roll_registry.execution_price(
                bar.instrument_id,
                instrument_id,
                as_of=bar.end_time,
            )
        except KeyError:
            return

    def _related_contracts_for(
        self, continuous_instrument_id: InstrumentId
    ) -> frozenset[InstrumentId]:
        related_contracts = self._related_contracts_by_continuous.get(continuous_instrument_id)
        if related_contracts is None:
            if self._future_roll_registry is None:
                raise RuntimeError("future roll registry is not configured")
            related_contracts = frozenset(
                self._future_roll_registry.related_contracts(continuous_instrument_id)
            )
            self._related_contracts_by_continuous[continuous_instrument_id] = related_contracts
        return related_contracts

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
        if self._instrument_registry is not None:
            return self._instrument_registry
        if not self._registry_bars:
            raise RuntimeError(
                "instrument_registry is required when backtest bars are streamed "
                "from a one-pass iterable"
            )
        registry = InstrumentRegistry()
        seen: set[InstrumentId] = set()
        for bar in self._registry_bars:
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
    def _history_limit_from_subscriptions(ctx: StrategyContext) -> int | None:
        if not ctx.subscriptions:
            return None
        return max(subscription.warmup for subscription in ctx.subscriptions)

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

    @staticmethod
    def _zero_time() -> Any:
        from datetime import UTC

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


__all__ = ["BacktestCostModel", "BacktestEngine", "BacktestStreamResult"]
