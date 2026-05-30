"""Backtest streaming sinks."""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from qts.core.hashing import stable_json_hash
from qts.domain.market_data import Bar
from qts.domain.orders import Order, OrderFill
from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint, TradeLedgerEntry
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext, RuntimeEventSink

if TYPE_CHECKING:
    from qts.observability.metrics import MetricsRegistry


class BacktestRuntimeEventSink(RuntimeEventSink):
    """Write engine stream artifacts through a shared writer."""

    _INGEST_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

    def __init__(
        self,
        writer: BacktestArtifactWriter,
        *,
        context: RuntimeEventContext | None = None,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        """Create a backtest sink for runtime events and derived artifacts.

        When ``metrics`` is supplied, every ``RuntimeEvent`` written through
        this sink is also classified into the standard counter set via
        :meth:`MetricsRegistry.record_runtime_event` so the Prometheus
        exporter sees populated data without a separate poller.
        """
        self._writer = writer
        self._context = context
        self._order_count = 0
        self._event_count = 0
        self._metrics = metrics
        self._last_market_data_perf_counter: float | None = None

    @property
    def order_count(self) -> int:
        """Return the number of orders written through this sink."""
        return self._order_count

    def write(self, event: RuntimeEvent) -> object:
        """Write one normalized runtime event envelope."""
        self._event_count += 1
        if self._context is not None:
            event = self._context.apply(event, sequence_no=self._event_count)
        deterministic_timestamp = self._INGEST_EPOCH + timedelta(microseconds=self._event_count)
        event = replace(
            event,
            ts_event=deterministic_timestamp,
            ts_ingest=deterministic_timestamp,
        )
        row = event.to_envelope(sequence_no=self._event_count)
        RuntimeEvent.require_canonical_envelope(row)
        row["event_hash"] = stable_json_hash(
            {key: value for key, value in row.items() if key not in {"sequence_no", "ts_ingest"}}
        )
        self._writer.write_runtime_event(row)
        if event.kind == "account.position_closed":
            self._writer.write_position_closed(dict(event.payload))
        if self._metrics is not None:
            self._metrics.record_runtime_event(event)
            self._observe_strategy_eval_latency(event)
        return self._event_count

    def _observe_strategy_eval_latency(self, event: RuntimeEvent) -> None:
        """Record strategy_eval_latency as the perf-counter delta between a bar's
        market_data emission and the first strategy signal it triggered.

        This is an approximate measure (it includes pipeline overhead, not just
        the strategy callback), but it gives a real wall-clock reading per bar
        rather than a sentinel.
        """
        if self._metrics is None:
            return
        from qts.observability.metrics import RuntimeLatencyMetric

        if event.kind == "runtime.market_data":
            self._last_market_data_perf_counter = time.perf_counter()
            return
        if (
            event.kind in {"runtime.signal_received", "runtime.strategy_intent"}
            and self._last_market_data_perf_counter is not None
        ):
            elapsed = time.perf_counter() - self._last_market_data_perf_counter
            self._metrics.record_latency(
                RuntimeLatencyMetric.STRATEGY_EVAL_LATENCY,
                max(elapsed, 0.0),
            )
            self._last_market_data_perf_counter = None

    def write_processed(
        self,
        *,
        orders: tuple[Order, ...],
        fills: tuple[OrderFill, ...],
        bar: Bar,
    ) -> None:
        """Write processed orders, fills, and trade-ledger rows for one bar."""
        for order in orders:
            self._writer.write_order(self._order_payload(order))
        for fill in fills:
            self._writer.write_fill(self._fill_payload(fill))
        for row in self._ledger_rows(fills, bar=bar):
            self._writer.write_trade_ledger(row)
        self._order_count += len(orders)

    def write_equity_point(self, point: EquityCurvePoint) -> None:
        """Write one equity-curve point through the writer."""
        self._writer.write_equity_point(point)

    def write_holdings_snapshot(
        self,
        *,
        gross_notional: object,
        net_notional: object,
    ) -> None:
        """Forward a per-bar holdings notional snapshot to the writer."""
        from decimal import Decimal as _Decimal

        self._writer.write_holdings_snapshot(
            gross_notional=_Decimal(str(gross_notional)),
            net_notional=_Decimal(str(net_notional)),
        )

    @staticmethod
    def _ledger_rows(fills: Iterable[OrderFill], *, bar: Bar) -> tuple[TradeLedgerEntry, ...]:
        """Build trade-ledger entries from fills timed to the given bar."""
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
        """Build the serializable artifact payload for an order."""
        return {
            "order_id": order.order_id.value,
            "instrument_id": order.intent.instrument_id.value,
            "side": order.intent.side.value,
            "quantity": str(order.intent.quantity),
            "order_spec": order.intent.order_spec.to_payload(),
            "state": order.state.value,
            "broker_order_id": order.broker_order_id,
        }

    @staticmethod
    def _fill_payload(fill: OrderFill) -> dict[str, Any]:
        """Build the serializable artifact payload for a fill."""
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


__all__ = ["BacktestRuntimeEventSink"]
