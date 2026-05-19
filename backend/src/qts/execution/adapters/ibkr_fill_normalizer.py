"""IBKR execution and commission callback normalization (fill staging)."""

from __future__ import annotations

from qts.domain.orders import ExecutionReport, ExecutionReportStatus
from qts.execution.adapters.broker_callback_quarantine import BrokerCallbackQuarantine
from qts.execution.adapters.ibkr_callback_types import (
    IbkrExecutionReport,
    IbkrOrderCallbackEvent,
    normalize_ibkr_execution_report,
    record_account_mismatch_event,
    record_callback_event,
)
from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
from qts.execution.broker import BrokerCommissionReport
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrCommissionPayload,
    IbkrExecutionPayload,
)


class IbkrFillNormalizer:
    """Owns IBKR execution/commission staging, fill assembly, and completion tracking."""

    def __init__(
        self,
        *,
        account_id: str,
        order_map: BrokerOrderMap | None,
        callback_events: list[IbkrOrderCallbackEvent],
        callback_quarantine: BrokerCallbackQuarantine,
    ) -> None:
        self._account_id = account_id
        self._order_map = order_map
        self._callback_events = callback_events
        self._callback_quarantine = callback_quarantine
        self._pending_executions: dict[tuple[str, str, str], IbkrExecutionPayload] = {}
        self._commissions: dict[str, IbkrCommissionPayload] = {}
        self._completed_execution_keys: set[tuple[str, str, str]] = set()

    def on_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Stage a raw IBKR execution callback until its commission arrives."""

        record_callback_event(
            self._callback_events,
            "ibkr_execution_details_received",
            report_id=payload.report_id,
            broker_order_id=payload.broker_order_id,
            execution_id=payload.execution_id,
        )
        if payload.account_id is not None and payload.account_id != self._account_id:
            self._callback_quarantine.add_execution(payload)
            record_account_mismatch_event(
                self._callback_events,
                self._account_id,
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                execution_id=payload.execution_id,
                observed_account=payload.account_id,
            )
            return None
        execution_key = self._execution_key(payload)
        if execution_key in self._completed_execution_keys:
            record_callback_event(
                self._callback_events,
                "ibkr_order_callback_duplicate_dropped",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                execution_id=payload.execution_id,
                reason="execution_already_completed",
            )
            return None
        if self._order_map is not None:
            try:
                self._order_map.by_ibkr_order_id(payload.broker_order_id)
            except KeyError:
                self._callback_quarantine.add_execution(payload)
                record_callback_event(
                    self._callback_events,
                    "ibkr_order_callback_unresolved_quarantined",
                    report_id=payload.report_id,
                    broker_order_id=payload.broker_order_id,
                    execution_id=payload.execution_id,
                    reason="unknown_ibkr_order_id",
                )
                return None
        self._pending_executions[execution_key] = payload
        commission = self._commissions.get(payload.execution_id)
        if commission is None:
            return None
        return self._pop_commissioned_execution(execution_key)

    def on_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | BrokerCommissionReport:
        """Normalize a raw IBKR commission callback and complete matching fills."""

        record_callback_event(
            self._callback_events,
            "ibkr_commission_report_received",
            execution_id=payload.execution_id,
        )
        self._commissions[payload.execution_id] = payload
        report = self._pop_commissioned_execution_by_execution_id(payload.execution_id)
        if report is not None:
            return report
        if any(key[2] == payload.execution_id for key in self._completed_execution_keys):
            record_callback_event(
                self._callback_events,
                "ibkr_order_callback_duplicate_dropped",
                execution_id=payload.execution_id,
                reason="commission_for_completed_execution",
            )
            return BrokerCommissionReport(
                execution_id=payload.execution_id,
                commission=payload.commission,
                currency=payload.currency,
            )
        return BrokerCommissionReport(
            execution_id=payload.execution_id,
            commission=payload.commission,
            currency=payload.currency,
        )

    def resolve_quarantined(self) -> tuple[ExecutionReport, ...]:
        """Try to resolve quarantined executions after order mapping changes."""
        resolved: list[ExecutionReport] = []
        unresolved: list[IbkrExecutionPayload] = []
        for execution_payload in self._callback_quarantine.executions:
            if (
                execution_payload.account_id is not None
                and execution_payload.account_id != self._account_id
            ):
                unresolved.append(execution_payload)
                continue
            if self._order_map is not None:
                try:
                    self._order_map.by_ibkr_order_id(execution_payload.broker_order_id)
                except KeyError:
                    unresolved.append(execution_payload)
                    continue
            execution_key = self._execution_key(execution_payload)
            if execution_key in self._completed_execution_keys:
                continue
            self._pending_executions[execution_key] = execution_payload
            report = self._pop_commissioned_execution(execution_key)
            if report is not None:
                resolved.append(report)
            record_callback_event(
                self._callback_events,
                "ibkr_order_callback_quarantine_resolved",
                report_id=execution_payload.report_id,
                broker_order_id=execution_payload.broker_order_id,
                execution_id=execution_payload.execution_id,
            )
        self._callback_quarantine.replace_executions(unresolved)
        return tuple(resolved)

    def _execution_key(self, payload: IbkrExecutionPayload) -> tuple[str, str, str]:
        account_id = payload.account_id or self._account_id
        return (account_id, payload.broker_order_id, payload.execution_id)

    def _pop_commissioned_execution_by_execution_id(
        self,
        execution_id: str,
    ) -> ExecutionReport | None:
        for execution_key in tuple(self._pending_executions):
            if execution_key[2] == execution_id:
                return self._pop_commissioned_execution(execution_key)
        return None

    def _pop_commissioned_execution(
        self,
        execution_key: tuple[str, str, str],
    ) -> ExecutionReport | None:
        execution = self._pending_executions.get(execution_key)
        commission = self._commissions.get(execution_key[2])
        if execution is None or commission is None:
            return None
        self._pending_executions.pop(execution_key)
        self._commissions.pop(execution_key[2])
        self._completed_execution_keys.add(execution_key)
        return normalize_ibkr_execution_report(
            IbkrExecutionReport(
                report_id=execution.report_id,
                broker_order_id=execution.broker_order_id,
                status=ExecutionReportStatus.FILLED,
                filled_quantity=execution.filled_quantity,
                fill_price=execution.fill_price,
                fill_id=execution.execution_id,
                commission=commission.commission,
                fill_time=execution.fill_time,
            )
        )


__all__ = ["IbkrFillNormalizer"]
