"""Backtest artifact service.

Owns the backtest run's artifact emission lifecycle: constructing the
partitioned artifact writer and the normalized runtime-event sink, recording
the bootstrap equity point for an empty run, and finalizing the manifest. The
engine orchestrates the actor loop between sink creation and finalization but
does not own ``qts.reporting`` artifact formats or ``qts.runtime.sinks`` event
plumbing directly.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from qts.core.ids import AccountId, RuntimeRunId, StrategyId
from qts.reporting.backtest import (
    BacktestArtifacts,
    BacktestArtifactWriter,
    EquityCurvePoint,
    zero_time,
)
from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
from qts.runtime.sinks.base import RuntimeEventContext

if TYPE_CHECKING:
    from qts.observability.metrics import MetricsRegistry


class BacktestArtifactService:
    """Own backtest artifact writing: the runtime event sink and final manifest."""

    def __init__(
        self,
        output_dir: Any,
        *,
        run_id: RuntimeRunId,
        account_id: AccountId,
        strategy_id: StrategyId | None,
        compact_events: bool = False,
        equity_curve_sample_interval: int = 1,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        """Create the writer + normalized event sink for a backtest run."""
        self._writer = BacktestArtifactWriter(
            output_dir,
            run_id=run_id,
            compact_events=compact_events,
            equity_curve_sample_interval=equity_curve_sample_interval,
        )
        self._sink = BacktestRuntimeEventSink(
            self._writer,
            context=RuntimeEventContext(
                run_id=run_id,
                mode="backtest",
                execution_environment="simulated",
                account_id=account_id,
                strategy_id=strategy_id,
            ),
            metrics=metrics,
        )

    @property
    def sink(self) -> BacktestRuntimeEventSink:
        """Return the sink the actor loop emits normalized events through."""
        return self._sink

    def record_empty_run_equity(
        self, *, equity: Decimal, last_bar_end_time: datetime | None
    ) -> None:
        """Bootstrap the equity curve for a run that processed zero bars."""
        self._sink.write_equity_point(
            EquityCurvePoint(
                time=last_bar_end_time if last_bar_end_time is not None else zero_time(),
                equity=equity,
            )
        )

    def finalize(
        self,
        *,
        config_hash: str,
        dataset_metadata: tuple[dict[str, Any], ...],
        cost_model: dict[str, Any],
        processed_bars: int,
        warmup_bars: int,
        trading_bars: int,
        final_cash: Decimal,
        strategy_version: str,
        runtime_topology_payload: dict[str, Any] | None = None,
        brokerage_model: str | None = None,
        execution_assumptions: dict[str, Any] | None = None,
        risk_config_hash: str | None = None,
        contract_economics_hash: str | None = None,
        margin_policy_hash: str | None = None,
    ) -> tuple[str, str, dict[str, Any], BacktestArtifacts]:
        """Finalize the manifest and return ``(run_id, report_hash, report, artifacts)``."""
        return self._writer.finalize(
            config_hash=config_hash,
            dataset_metadata=dataset_metadata,
            cost_model=cost_model,
            processed_bars=processed_bars,
            warmup_bars=warmup_bars,
            trading_bars=trading_bars,
            final_cash=final_cash,
            strategy_version=strategy_version,
            runtime_topology_payload=runtime_topology_payload,
            brokerage_model=brokerage_model,
            execution_assumptions=execution_assumptions,
            risk_config_hash=risk_config_hash,
            contract_economics_hash=contract_economics_hash,
            margin_policy_hash=margin_policy_hash,
        )


__all__ = ["BacktestArtifactService"]
