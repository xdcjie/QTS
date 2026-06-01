"""Anchor: a backtest run populates MetricsRegistry counters and latencies.

Domain fact: ``MetricsRegistry`` is wired into the same path that writes
runtime events to the sink, so a real backtest run produces a non-empty
snapshot. The Prometheus exporter then exposes those metrics through
``/metrics`` without any external poller.

Owner: ``BacktestRuntimeEventSink`` (sink-level event counts) +
``BacktestActorLoop`` (latency observations + mailbox depth gauge).

Forbidden shortcut: polling actor state externally; a separate metrics
emitter that doesn't see the canonical bar timestamp.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar
from qts.observability.metrics import (
    MetricsRegistry,
    RuntimeCounterMetric,
    RuntimeLatencyMetric,
)


def _bar(start: datetime, close: str) -> Bar:
    from qts.core.ids import InstrumentId

    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_backtest_run_populates_metrics_registry(tmp_path: Path) -> None:
    from qts.strategy_sdk import Strategy

    from tests.support.backtest_engine import backtest_engine_from_inputs

    class _BuyOnce(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.opened = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            if not self.opened:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.opened = True

    metrics = MetricsRegistry()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    engine = backtest_engine_from_inputs(
        strategy=_BuyOnce(),
        bars=[_bar(start + timedelta(minutes=i), "100") for i in range(3)],
        initial_cash=Decimal("100000"),
    )
    engine.run_streaming(tmp_path / "metrics-run", metrics=metrics)

    snapshot = metrics.snapshot()
    # Sink records every RuntimeEvent through MetricsRegistry.record_runtime_event,
    # which classifies kinds into the standard counter set.
    assert any(name.startswith("market_data") for name in snapshot)
    assert any(name.startswith("fills_total") for name in snapshot)
    # Strategy evaluation latency is observed at least once.
    assert RuntimeLatencyMetric.STRATEGY_EVAL_LATENCY.value in {
        name.split("{")[0] for name in snapshot
    }
    # Mailbox depth gauge is intentionally deferred to a follow-up that needs
    # actor-internal mailbox access; OPT-57 first slice ships sink-level wiring.


def test_sink_records_runtime_event_into_metrics_registry() -> None:
    import tempfile
    from pathlib import Path

    from qts.core.ids import CorrelationId, RuntimeRunId
    from qts.observability.metrics import MetricsRegistry
    from qts.reporting.backtest import BacktestArtifactWriter
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext

    with tempfile.TemporaryDirectory() as tmp:
        writer = BacktestArtifactWriter(Path(tmp))
        metrics = MetricsRegistry()
        sink = BacktestRuntimeEventSink(
            writer,
            context=RuntimeEventContext(
                run_id=RuntimeRunId("run-1"),
                mode="backtest",
                execution_environment="simulated",
            ),
            metrics=metrics,
        )
        sink.write(
            RuntimeEvent(
                kind="runtime.order_submitted",
                payload={"order_id": "ord-1", "client_order_id": "cli-1"},
                correlation_id=CorrelationId("corr-1"),
            )
        )

        snapshot = metrics.snapshot()
        assert snapshot.get(RuntimeCounterMetric.ORDERS_SUBMITTED_TOTAL.value) == 1
