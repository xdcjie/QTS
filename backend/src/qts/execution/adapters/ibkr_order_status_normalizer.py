"""IBKR order-status and open-order callback normalization."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import OrderId
from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderSide
from qts.execution.adapters.broker_callback_quarantine import BrokerCallbackQuarantine
from qts.execution.adapters.ibkr_callback_types import (
    IbkrExecutionReport,
    IbkrOrderCallbackEvent,
    normalize_ibkr_execution_report,
    record_callback_event,
)
from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrOpenOrderPayload,
    IbkrOrderStatusPayload,
)
from qts.reconciliation.snapshots import OrderSnapshot
from qts.registry.broker_symbol_mapping import BrokerSymbolMapping


class IbkrOrderStatusNormalizer:
    """Owns IBKR order-status deduplication, open-order tracking, and order snapshots."""

    def __init__(
        self,
        *,
        account_id: str,
        symbol_mapping: BrokerSymbolMapping,
        order_map: BrokerOrderMap | None,
        callback_events: list[IbkrOrderCallbackEvent],
        callback_quarantine: BrokerCallbackQuarantine,
    ) -> None:
        self._account_id = account_id
        self._symbol_mapping = symbol_mapping
        self._order_map = order_map
        self._callback_events = callback_events
        self._callback_quarantine = callback_quarantine
        self._seen_order_status_keys: set[tuple[str, str, str | None]] = set()
        self._seen_open_order_keys: set[
            tuple[str, str | None, str | None, str | None, str | None, str | None, Decimal | None]
        ] = set()
        self._broker_open_orders: dict[OrderId, OrderSnapshot] = {}

    @property
    def broker_open_orders(self) -> dict[OrderId, OrderSnapshot]:
        """Read-only access to tracked broker open orders."""
        return self._broker_open_orders

    def on_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Normalize a raw IBKR order-status callback."""

        record_callback_event(
            self._callback_events,
            "ibkr_order_status_received",
            report_id=payload.report_id,
            broker_order_id=payload.broker_order_id,
        )
        status_key = (payload.broker_order_id, payload.status, payload.perm_id)
        if status_key in self._seen_order_status_keys:
            record_callback_event(
                self._callback_events,
                "ibkr_order_callback_duplicate_dropped",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                reason="order_status_already_seen",
            )
            return None
        if self._order_map is not None:
            try:
                if payload.perm_id is not None:
                    self._order_map.attach_perm_id(
                        ibkr_order_id=payload.broker_order_id,
                        perm_id=payload.perm_id,
                    )
                record = self._order_map.by_ibkr_order_id(payload.broker_order_id)
                if self._is_late_cancel_after_fill(
                    current_status=record.status,
                    next_status=payload.status,
                ):
                    record_callback_event(
                        self._callback_events,
                        "ibkr_order_callback_late_terminal_dropped",
                        report_id=payload.report_id,
                        broker_order_id=payload.broker_order_id,
                        reason="late_cancel_after_filled",
                    )
                    return None
                self._order_map.mark_status(
                    ibkr_order_id=payload.broker_order_id,
                    status=payload.status,
                    last_broker_status_at=datetime.now(UTC),
                )
            except KeyError:
                self._callback_quarantine.add_order_status(payload)
                record_callback_event(
                    self._callback_events,
                    "ibkr_order_callback_unresolved_quarantined",
                    report_id=payload.report_id,
                    broker_order_id=payload.broker_order_id,
                    reason="unknown_ibkr_order_id",
                )
                return None
        self._seen_order_status_keys.add(status_key)
        return normalize_ibkr_execution_report(
            IbkrExecutionReport(
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                status=self._status_from_ibkr(payload.status),
            )
        )

    def on_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Record an IBKR openOrder callback against the broker-order map."""

        record_callback_event(
            self._callback_events,
            "ibkr_open_order_received",
            report_id=payload.report_id,
            broker_order_id=payload.broker_order_id,
        )
        if self._order_map is None:
            return
        if payload.client_order_id is None:
            self._callback_quarantine.add_open_order(payload)
            record_callback_event(
                self._callback_events,
                "ibkr_order_callback_unresolved_quarantined",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                reason="missing_client_order_id",
            )
            return
        try:
            open_order_key = self._open_order_key(payload)
            if open_order_key in self._seen_open_order_keys:
                record_callback_event(
                    self._callback_events,
                    "ibkr_order_callback_duplicate_dropped",
                    report_id=payload.report_id,
                    broker_order_id=payload.broker_order_id,
                    reason="open_order_already_seen",
                )
                return
            record = self._order_map.by_client_order_id(payload.client_order_id)
            self._order_map.attach_ibkr_order_id(
                client_order_id=payload.client_order_id,
                ibkr_order_id=payload.broker_order_id,
            )
            if payload.perm_id is not None:
                self._order_map.attach_perm_id(
                    ibkr_order_id=payload.broker_order_id,
                    perm_id=payload.perm_id,
                )
            if payload.status is not None:
                self._order_map.mark_status(
                    ibkr_order_id=payload.broker_order_id,
                    status=payload.status,
                    last_broker_status_at=datetime.now(UTC),
                )
            if (
                payload.broker_symbol is not None
                and payload.side is not None
                and payload.quantity is not None
                and payload.status is not None
            ):
                self._broker_open_orders[record.internal_order_id] = OrderSnapshot(
                    order_id=record.internal_order_id,
                    instrument_id=self._symbol_mapping.to_instrument_id(payload.broker_symbol),
                    side=self._order_side_from_ibkr(payload.side),
                    quantity=payload.quantity,
                    status=payload.status,
                )
            self._seen_open_order_keys.add(open_order_key)
        except KeyError:
            self._callback_quarantine.add_open_order(payload)
            record_callback_event(
                self._callback_events,
                "ibkr_order_callback_unresolved_quarantined",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                reason="unknown_client_order_id",
            )

    def resolve_quarantined(self) -> tuple[ExecutionReport, ...]:
        """Try to resolve quarantined open orders and order statuses."""
        resolved: list[ExecutionReport] = []

        unresolved_open_orders: list[IbkrOpenOrderPayload] = []
        for open_order_payload in self._callback_quarantine.open_orders:
            before_count = len(self._callback_quarantine.open_orders)
            self.on_open_order(open_order_payload)
            if len(self._callback_quarantine.open_orders) > before_count:
                self._callback_quarantine.replace_open_orders(
                    list(self._callback_quarantine.open_orders[:-1])
                )
                unresolved_open_orders.append(open_order_payload)
        self._callback_quarantine.replace_open_orders(unresolved_open_orders)

        unresolved_order_statuses: list[IbkrOrderStatusPayload] = []
        for order_status_payload in self._callback_quarantine.order_statuses:
            before_count = len(self._callback_quarantine.order_statuses)
            report = self.on_order_status(order_status_payload)
            if report is not None:
                resolved.append(report)
            if len(self._callback_quarantine.order_statuses) > before_count:
                self._callback_quarantine.replace_order_statuses(
                    list(self._callback_quarantine.order_statuses[:-1])
                )
                unresolved_order_statuses.append(order_status_payload)
        self._callback_quarantine.replace_order_statuses(unresolved_order_statuses)

        return tuple(resolved)

    @staticmethod
    def _status_from_ibkr(status: str) -> ExecutionReportStatus:
        normalized = status.strip().lower()
        status_map = {
            "apicancelled": ExecutionReportStatus.CANCELLED,
            "cancelled": ExecutionReportStatus.CANCELLED,
            "filled": ExecutionReportStatus.FILLED,
            "inactive": ExecutionReportStatus.REJECTED,
            "pendingcancel": ExecutionReportStatus.ACCEPTED,
            "pendingsubmit": ExecutionReportStatus.ACCEPTED,
            "presubmitted": ExecutionReportStatus.ACCEPTED,
            "submitted": ExecutionReportStatus.ACCEPTED,
        }
        try:
            return status_map[normalized]
        except KeyError as exc:
            raise ValueError(f"unsupported IBKR order status: {status}") from exc

    @staticmethod
    def _order_side_from_ibkr(side: str) -> OrderSide:
        normalized = side.strip().lower()
        if normalized in {"buy", "bot"}:
            return OrderSide.BUY
        if normalized in {"sell", "sld"}:
            return OrderSide.SELL
        raise ValueError(f"unsupported IBKR order side: {side}")

    @staticmethod
    def _open_order_key(
        payload: IbkrOpenOrderPayload,
    ) -> tuple[str, str | None, str | None, str | None, str | None, str | None, Decimal | None]:
        return (
            payload.broker_order_id,
            payload.client_order_id,
            payload.perm_id,
            payload.status,
            payload.broker_symbol,
            payload.side,
            payload.quantity,
        )

    @staticmethod
    def _is_late_cancel_after_fill(*, current_status: str, next_status: str) -> bool:
        return current_status.strip().lower() == "filled" and next_status.strip().lower() in {
            "apicancelled",
            "cancelled",
        }


__all__ = ["IbkrOrderStatusNormalizer"]
