"""Backtest streaming sinks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.domain.market_data import Bar
from qts.execution.order_manager import Order, OrderFill
from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint, TradeLedgerEntry
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext, RuntimeEventSink


class BacktestRuntimeEventSink(RuntimeEventSink):
    """Write engine stream artifacts through a shared writer."""

    _INGEST_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

    def __init__(
        self,
        writer: BacktestArtifactWriter,
        *,
        context: RuntimeEventContext | None = None,
    ) -> None:
        """Create a backtest sink for runtime events and derived artifacts."""
        self._writer = writer
        self._context = context
        self._order_count = 0
        self._event_count = 0

    @property
    def order_count(self) -> int:
        """Perform order_count."""
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
        return self._event_count

    def write_processed(
        self,
        *,
        orders: tuple[Order, ...],
        fills: tuple[OrderFill, ...],
        bar: Bar,
    ) -> None:
        """Perform write_processed."""
        for order in orders:
            self._writer.write_order(self._order_payload(order))
        for fill in fills:
            self._writer.write_fill(self._fill_payload(fill))
        for row in self._ledger_rows(fills, bar=bar):
            self._writer.write_trade_ledger(row)
        self._order_count += len(orders)

    def write_equity_point(self, point: EquityCurvePoint) -> None:
        """Perform write_equity_point."""
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
        """Perform _ledger_rows."""
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
        """Perform _order_payload."""
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
        """Perform _fill_payload."""
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
