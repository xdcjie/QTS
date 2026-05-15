"""IBKR TWS order-execution event emitter."""

from __future__ import annotations

import queue

from qts.domain.orders import ExecutionReport
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
)


class IbkrTwsExecutionEventEmitter:
    """Owns adapter sink dispatch and report/error queue publication."""

    def __init__(
        self,
        *,
        sink: IbkrOrderExecutionCallbackSink,
        reports: queue.Queue[ExecutionReport | IbkrTransportError | IbkrConnectionEvent],
    ) -> None:
        self._sink = sink
        self._reports = reports

    def emit_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Dispatch a raw order-status callback to the adapter sink."""

        report = self._sink.on_order_status(payload)
        if report is not None:
            self._reports.put(report)
        return report

    def emit_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Dispatch a raw openOrder callback to the adapter sink."""

        self._sink.on_open_order(payload)

    def emit_position(self, payload: IbkrPositionPayload) -> None:
        """Dispatch a raw position callback to the adapter sink."""

        self._sink.on_position(payload)

    def emit_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Dispatch a raw accountSummary callback to the adapter sink."""

        self._sink.on_account_summary(payload)

    def emit_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Dispatch a raw execution callback to the adapter sink."""

        report = self._sink.on_execution(payload)
        if report is not None:
            self._reports.put(report)
        return report

    def emit_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Dispatch a raw commission callback to the adapter sink."""

        return self._sink.on_commission(payload)

    def emit_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        """Dispatch a raw error callback to the adapter sink."""

        return self._sink.on_error(payload)

    def publish_error(self, payload: IbkrErrorPayload) -> None:
        """Dispatch and publish a raw error callback."""

        self._reports.put(self.emit_error(payload))

    def emit_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw disconnect callback to the adapter sink."""

        return self._sink.on_disconnect(payload)

    def publish_disconnect(self, payload: IbkrConnectionEventPayload) -> None:
        """Dispatch and publish a raw disconnect callback."""

        self._reports.put(self.emit_disconnect(payload))

    def emit_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw reconnect callback to the adapter sink."""

        return self._sink.on_reconnect(payload)

    def publish_reconnect(self, payload: IbkrConnectionEventPayload) -> None:
        """Dispatch and publish a raw reconnect callback."""

        self._reports.put(self.emit_reconnect(payload))

    def publish_commission_result(
        self,
        result: ExecutionReport | IbkrCommissionReport,
    ) -> None:
        """Publish a completed fill report produced by a commission callback."""

        if isinstance(result, ExecutionReport):
            self._reports.put(result)


__all__ = ["IbkrTwsExecutionEventEmitter"]
