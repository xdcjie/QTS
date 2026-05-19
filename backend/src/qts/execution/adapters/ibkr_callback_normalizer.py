"""IBKR callback normalization and reconciliation projection (facade)."""

from __future__ import annotations

from qts.core.ids import AccountId
from qts.domain.orders import ExecutionReport
from qts.execution.adapters.broker_callback_quarantine import BrokerCallbackQuarantine
from qts.execution.adapters.ibkr_callback_types import (
    IbkrExecutionReport,
    IbkrOrderCallbackEvent,
    normalize_ibkr_execution_report,
)
from qts.execution.adapters.ibkr_fill_normalizer import IbkrFillNormalizer
from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
from qts.execution.adapters.ibkr_order_status_normalizer import IbkrOrderStatusNormalizer
from qts.execution.adapters.ibkr_position_recorder import IbkrPositionRecorder
from qts.execution.broker import BrokerCommissionReport
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrAccountSummaryPayload,
    IbkrCommissionPayload,
    IbkrExecutionPayload,
    IbkrOpenOrderPayload,
    IbkrOrderStatusPayload,
    IbkrPositionPayload,
)
from qts.reconciliation.snapshots import ReconciliationSnapshot
from qts.registry.broker_symbol_mapping import BrokerSymbolMapping


class IbkrCallbackNormalizer:
    """Owns IBKR callback idempotency, quarantine, and normalized projections.

    Thin facade that delegates to three cohesive components:
    - IbkrOrderStatusNormalizer: order-status deduplication and open-order tracking
    - IbkrFillNormalizer: execution/commission staging and fill assembly
    - IbkrPositionRecorder: position and cash recording for reconciliation
    """

    def __init__(
        self,
        *,
        account_id: str,
        symbol_mapping: BrokerSymbolMapping,
        order_map: BrokerOrderMap | None = None,
    ) -> None:
        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        self._account_id = account_id
        self._symbol_mapping = symbol_mapping
        self._order_map = order_map
        self._callback_events: list[IbkrOrderCallbackEvent] = []
        self._callback_quarantine = BrokerCallbackQuarantine()
        self._order_status_normalizer = IbkrOrderStatusNormalizer(
            account_id=account_id,
            symbol_mapping=symbol_mapping,
            order_map=order_map,
            callback_events=self._callback_events,
            callback_quarantine=self._callback_quarantine,
        )
        self._fill_normalizer = IbkrFillNormalizer(
            account_id=account_id,
            order_map=order_map,
            callback_events=self._callback_events,
            callback_quarantine=self._callback_quarantine,
        )
        self._position_recorder = IbkrPositionRecorder(
            account_id=account_id,
            symbol_mapping=symbol_mapping,
            callback_events=self._callback_events,
            callback_quarantine=self._callback_quarantine,
        )

    @property
    def quarantined_executions(self) -> tuple[IbkrExecutionPayload, ...]:
        """Read-only unresolved IBKR execution callbacks."""
        return self._callback_quarantine.executions

    @property
    def quarantined_open_orders(self) -> tuple[IbkrOpenOrderPayload, ...]:
        """Read-only unresolved IBKR openOrder callbacks."""
        return self._callback_quarantine.open_orders

    @property
    def quarantined_order_statuses(self) -> tuple[IbkrOrderStatusPayload, ...]:
        """Read-only unresolved IBKR order-status callbacks."""
        return self._callback_quarantine.order_statuses

    @property
    def quarantined_positions(self) -> tuple[IbkrPositionPayload, ...]:
        """Read-only unresolved IBKR position callbacks."""
        return self._callback_quarantine.positions

    @property
    def quarantined_account_summaries(self) -> tuple[IbkrAccountSummaryPayload, ...]:
        """Read-only unresolved IBKR account-summary callbacks."""
        return self._callback_quarantine.account_summaries

    @property
    def callback_events(self) -> tuple[IbkrOrderCallbackEvent, ...]:
        """Read-only IBKR callback audit events."""
        return tuple(self._callback_events)

    @property
    def has_unresolved_callbacks(self) -> bool:
        """Return whether unresolved IBKR callbacks remain quarantined."""

        return self._callback_quarantine.has_unresolved

    def validate_no_unresolved_callbacks(self) -> None:
        """Fail closed while broker callbacks remain unresolved."""

        if self.has_unresolved_callbacks:
            raise RuntimeError("unresolved IBKR callbacks require reconciliation before new orders")

    def normalize_execution_report(self, report: IbkrExecutionReport) -> ExecutionReport:
        """Normalize an IBKR execution report to the internal execution report."""

        return normalize_ibkr_execution_report(report)

    def on_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Normalize a raw IBKR order-status callback."""

        return self._order_status_normalizer.on_order_status(payload)

    def on_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Record an IBKR openOrder callback against the broker-order map."""

        self._order_status_normalizer.on_open_order(payload)

    def on_position(self, payload: IbkrPositionPayload) -> None:
        """Record an IBKR position callback for broker reconciliation."""

        self._position_recorder.on_position(payload)

    def on_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Record an IBKR account summary callback for broker reconciliation."""

        self._position_recorder.on_account_summary(payload)

    def broker_reconciliation_snapshot(
        self,
        *,
        account_id: AccountId,
    ) -> ReconciliationSnapshot:
        """Return the latest normalized broker-side snapshot for reconciliation."""

        open_orders = self._order_status_normalizer.broker_open_orders
        positions = self._position_recorder.broker_positions
        cash = self._position_recorder.broker_cash
        return ReconciliationSnapshot(
            account_id=account_id,
            orders=tuple(
                open_orders[order_id]
                for order_id in sorted(open_orders, key=lambda item: item.value)
            ),
            positions=tuple(positions[instrument_id] for instrument_id in sorted(positions)),
            cash=tuple(cash[currency] for currency in sorted(cash)),
        )

    def on_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Stage a raw IBKR execution callback until its commission arrives."""

        return self._fill_normalizer.on_execution(payload)

    def on_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | BrokerCommissionReport:
        """Normalize a raw IBKR commission callback and complete matching fills."""

        return self._fill_normalizer.on_commission(payload)

    def resolve_quarantined_callbacks(self) -> tuple[ExecutionReport, ...]:
        """Try to resolve quarantined callbacks after order mapping changes."""

        reports = list(self._order_status_normalizer.resolve_quarantined())
        reports.extend(self._fill_normalizer.resolve_quarantined())
        reports.extend(self._position_recorder.resolve_quarantined())
        return tuple(reports)


__all__ = [
    "IbkrCallbackNormalizer",
    "IbkrExecutionReport",
    "IbkrOrderCallbackEvent",
]
