"""Backtest engine."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, tzinfo
from decimal import Decimal
from typing import Any

from qts.backtest.actor_loop import BacktestActorLoop
from qts.backtest.config import BacktestRunConfig
from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.backtest.intent_processor import BacktestIntentProcessor
from qts.backtest.portfolio_projection import BacktestPortfolioProjector
from qts.backtest.report import (
    EquityCurvePoint,
    StreamingBacktestArtifactWriter,
)
from qts.backtest.sinks import BacktestStreamingSink
from qts.core.hashing import stable_json_hash
from qts.core.ids import BacktestRunId, InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.domain.market_data import Bar
from qts.execution.order_manager import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
)
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actors.account_actor import AccountSnapshot
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
from qts.strategy_sdk import Strategy


@dataclass(frozen=True, slots=True)
class BacktestCostModel:
    """Explicit simulation cost assumptions included in reports."""

    fixed_commission_per_contract: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")
    latency_model: str = "zero"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.fixed_commission_per_contract < Decimal("0"):
            raise ValueError("fixed_commission_per_contract must be non-negative")
        if self.slippage_bps < Decimal("0"):
            raise ValueError("slippage_bps must be non-negative")
        if not self.latency_model.strip():
            raise ValueError("latency_model must not be empty")

    def to_payload(self) -> dict[str, str]:
        """Perform to_payload."""
        return {
            "fixed_commission_per_contract": str(self.fixed_commission_per_contract),
            "slippage_bps": str(self.slippage_bps),
            "latency_model": self.latency_model,
        }

    @property
    def slippage_model(self) -> str:
        """Perform slippage_model."""
        return "zero" if self.slippage_bps == Decimal("0") else "basis_points"

    @property
    def commission_model(self) -> str:
        """Perform commission_model."""
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
        """Perform __init__."""
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
        self._risk_engine = risk_engine or RiskEngine(
            [MaxNotionalRule(max_notional=initial_cash * Decimal("100"))]
        )
        self._instrument_context = BacktestInstrumentContext(
            future_roll_registry=self._future_roll_registry,
            instrument_registry=instrument_registry,
            registry_bars=self._registry_bars,
            contract_multipliers=self._contract_multipliers,
        )
        self._portfolio_projector = BacktestPortfolioProjector(
            contract_multipliers=self._contract_multipliers
        )
        self._intent_processor = BacktestIntentProcessor(
            risk_engine=self._risk_engine,
            instrument_context=self._instrument_context,
            multiplier_for=self._portfolio_projector.multiplier_for,
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
        """Perform from_config."""
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

    def run_streaming(self, output_dir: Any) -> BacktestStreamResult:
        """Perform run_streaming."""
        writer = StreamingBacktestArtifactWriter(output_dir)
        sink = BacktestStreamingSink(writer)
        actor_loop = BacktestActorLoop(
            strategy=self._strategy,
            bars=self._bars,
            initial_cash=self._initial_cash,
            target_timeframe=self._target_timeframe,
            exchange_timezone_by_instrument=self._exchange_timezone_by_instrument,
            warmup_bars=self._warmup_bars,
            instrument_registry=self._instrument_context.instrument_registry(),
            future_roll_registry=self._future_roll_registry,
            contract_multipliers=self._contract_multipliers,
            execution_adapter=_BacktestExecutionAdapter(self._cost_model),
            process_intent=self._intent_processor.process_intent,
            portfolio_view=self._portfolio_projector.portfolio_view,
            equity_point=self._portfolio_projector.equity_point,
            update_rolling_prices=self._instrument_context.update_rolling_prices,
        )
        runtime = actor_loop.run(
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
        config_hash = stable_json_hash(self._config)
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

    @staticmethod
    def _dataset_payload(item: DatasetMetadata) -> dict[str, Any]:
        """Perform _dataset_payload."""
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
    def _zero_time() -> Any:
        """Perform _zero_time."""
        from datetime import UTC

        return datetime(1970, 1, 1, tzinfo=UTC)


class _BacktestExecutionAdapter:
    """_BacktestExecutionAdapter."""
    def __init__(self, cost_model: BacktestCostModel) -> None:
        """Perform __init__."""
        self._cost_model = cost_model

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        """Perform execute_market_order."""
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


__all__ = [
    "BacktestCostModel",
    "BacktestEngine",
    "BacktestStreamResult",
    "SignalAggregatorActor",
    "StrategyActor",
    "StrategyBarEvent",
    "StrategyBarResult",
    "StrategyFinalize",
    "StrategyFinalized",
    "AggregatedSignalBatch",
    "StrategySignalEvent",
]
