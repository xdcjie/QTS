"""IBKR TWS callback dispatcher for order execution."""

from __future__ import annotations

from typing import Any

from qts.domain.orders import ExecutionReport
from qts.execution.transports.ibkr_tws_execution_event_emitter import (
    IbkrTwsExecutionEventEmitter,
)
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrAccountSummaryPayload,
    IbkrCommissionPayload,
    IbkrCommissionReport,
    IbkrConnectionEvent,
    IbkrConnectionEventPayload,
    IbkrErrorPayload,
    IbkrExecutionPayload,
    IbkrOpenOrderPayload,
    IbkrOrderExecutionCallbackSink,
    IbkrOrderStatusPayload,
    IbkrPositionPayload,
    IbkrTransportError,
    _to_decimal,
)

_ORDER_STATUS_REPORT_PREFIX = "ibkr-status"
_EXECUTION_REPORT_PREFIX = "ibkr-exec"


class IbkrTwsCallbackDispatcher:
    """Converts raw TWS callbacks into transport payloads and emits them."""

    def __init__(
        self,
        *,
        sink: IbkrOrderExecutionCallbackSink,
        emitter: IbkrTwsExecutionEventEmitter,
    ) -> None:
        self._sink = sink
        self._emitter = emitter

    def dispatch_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Route a normalized order-status callback payload."""

        report = self._sink.on_order_status(payload)
        self._emitter.publish_report(report)
        return report

    def dispatch_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Route a normalized openOrder callback payload."""

        self._sink.on_open_order(payload)

    def dispatch_position(self, payload: IbkrPositionPayload) -> None:
        """Route a normalized position callback payload."""

        self._sink.on_position(payload)

    def dispatch_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Route a normalized accountSummary callback payload."""

        self._sink.on_account_summary(payload)

    def dispatch_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Route a normalized execution callback payload."""

        report = self._sink.on_execution(payload)
        self._emitter.publish_report(report)
        return report

    def dispatch_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Route a normalized commission callback payload."""

        result = self._sink.on_commission(payload)
        self._emitter.publish_commission_result(result)
        return result

    def dispatch_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        """Route a normalized error callback payload."""

        return self._sink.on_error(payload)

    def dispatch_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Route a normalized disconnect callback payload."""

        return self._sink.on_disconnect(payload)

    def dispatch_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Route a normalized reconnect callback payload."""

        return self._sink.on_reconnect(payload)

    def handle_order_status(
        self,
        *,
        order_id: int,
        status: str,
        perm_id: int | None = None,
    ) -> ExecutionReport | None:
        """Handle an IBKR orderStatus callback."""

        return self.dispatch_order_status(
            IbkrOrderStatusPayload(
                report_id=f"{_ORDER_STATUS_REPORT_PREFIX}-{order_id}-{status.lower()}",
                broker_order_id=str(order_id),
                status=status,
                perm_id=None if perm_id is None else str(perm_id),
            )
        )

    def handle_open_order(
        self,
        *,
        order_id: int,
        order: Any,
        order_state: Any,
        contract: Any | None = None,
    ) -> None:
        """Handle an IBKR openOrder callback."""

        order_ref = str(getattr(order, "orderRef", "")).strip()
        perm_id = getattr(order, "permId", None)
        status = str(getattr(order_state, "status", "")).strip()
        total_quantity = order.totalQuantity if hasattr(order, "totalQuantity") else None
        self.dispatch_open_order(
            IbkrOpenOrderPayload(
                report_id=f"ibkr-open-order-{order_id}",
                broker_order_id=str(order_id),
                client_order_id=order_ref or None,
                perm_id=None if perm_id in {None, 0, ""} else str(perm_id),
                status=status or None,
                broker_symbol=(
                    str(getattr(contract, "symbol", "")).strip() if contract is not None else None
                )
                or None,
                side=str(getattr(order, "action", "")).strip() or None,
                quantity=None if total_quantity in {None, ""} else _to_decimal(total_quantity),
            )
        )

    def handle_position(self, *, account_id: str, contract: Any, position: object) -> None:
        """Handle an IBKR position callback."""

        self.dispatch_position(
            IbkrPositionPayload(
                account_id=account_id,
                broker_symbol=str(getattr(contract, "symbol", "")).strip(),
                quantity=_to_decimal(position),
            )
        )

    def handle_account_summary(
        self,
        *,
        account_id: str,
        tag: str,
        value: object,
        currency: str,
    ) -> None:
        """Handle an IBKR accountSummary callback."""

        self.dispatch_account_summary(
            IbkrAccountSummaryPayload(
                account_id=account_id,
                tag=tag,
                value=_to_decimal(value),
                currency=currency,
            )
        )

    def handle_execution(self, execution: Any) -> ExecutionReport | None:
        """Handle an IBKR execDetails callback."""

        return self.dispatch_execution(
            IbkrExecutionPayload(
                report_id=f"{_EXECUTION_REPORT_PREFIX}-{execution.execId}",
                broker_order_id=str(execution.orderId),
                execution_id=str(execution.execId),
                filled_quantity=_to_decimal(execution.shares),
                fill_price=_to_decimal(execution.price),
                account_id=(
                    str(getattr(execution, "acctNumber", "")).strip()
                    if hasattr(execution, "acctNumber")
                    else None
                )
                or None,
            )
        )

    def handle_commission_report(self, commission_report: Any) -> None:
        """Handle an IBKR commission callback."""

        commission = (
            commission_report.commissionAndFees
            if hasattr(commission_report, "commissionAndFees")
            else commission_report.commission
        )
        self.dispatch_commission(
            IbkrCommissionPayload(
                execution_id=str(commission_report.execId),
                commission=_to_decimal(commission),
                currency=str(commission_report.currency),
            )
        )

    def handle_commission_and_fees(self, commission_report: Any) -> None:
        """Handle an IBKR commissionAndFeesReport callback."""

        self.handle_commission_report(commission_report)

    def handle_error(self, *, request_id: int, code: int, message: str) -> None:
        """Handle an IBKR error callback."""

        if message.strip():
            self._emitter.publish_error(
                self.dispatch_error(
                    IbkrErrorPayload(request_id=request_id, code=code, message=message)
                )
            )

    def handle_disconnect(self, *, reason: str) -> None:
        """Handle an IBKR disconnect callback."""

        self._emitter.publish_disconnect(
            self.dispatch_disconnect(IbkrConnectionEventPayload(reason=reason))
        )

    def handle_reconnect(self, *, reason: str) -> None:
        """Handle an IBKR reconnect callback."""

        self._emitter.publish_reconnect(
            self.dispatch_reconnect(IbkrConnectionEventPayload(reason=reason))
        )


__all__ = ["IbkrTwsCallbackDispatcher"]
