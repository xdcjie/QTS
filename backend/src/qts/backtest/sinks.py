"""Backtest streaming sinks."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from qts.backtest.report import EquityCurvePoint, StreamingBacktestArtifactWriter, TradeLedgerEntry
from qts.domain.market_data import Bar
from qts.execution.order_manager import Order, OrderFill


class BacktestStreamingSink:
    """Write engine stream artifacts through a shared writer."""

    def __init__(self, writer: StreamingBacktestArtifactWriter) -> None:
        """Perform __init__."""
        self._writer = writer
        self._order_count = 0

    @property
    def order_count(self) -> int:
        """Perform order_count."""
        return self._order_count

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


__all__ = ["BacktestStreamingSink"]
