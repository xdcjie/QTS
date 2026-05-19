"""IBKR TWS order-execution event emitter."""

from __future__ import annotations

import queue

from qts.domain.orders import ExecutionReport
from qts.execution.broker import BrokerCommissionReport
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrConnectionEvent,
    IbkrTransportError,
)


class IbkrTwsExecutionEventEmitter:
    """Publishes normalized order-execution transport events."""

    def __init__(
        self,
        *,
        reports: queue.Queue[ExecutionReport | IbkrTransportError | IbkrConnectionEvent],
    ) -> None:
        self._reports = reports

    def publish_report(self, report: ExecutionReport | None) -> None:
        """Publish a normalized execution report when one is available."""

        if report is not None:
            self._reports.put(report)

    def publish_error(self, error: IbkrTransportError) -> None:
        """Publish a normalized transport error."""

        self._reports.put(error)

    def publish_disconnect(self, event: IbkrConnectionEvent) -> None:
        """Publish a normalized disconnect event."""

        self._reports.put(event)

    def publish_reconnect(self, event: IbkrConnectionEvent) -> None:
        """Publish a normalized reconnect event."""

        self._reports.put(event)

    def publish_commission_result(
        self,
        result: ExecutionReport | BrokerCommissionReport,
    ) -> None:
        """Publish a normalized fill report produced by a commission callback."""

        self.publish_report(result if isinstance(result, ExecutionReport) else None)


__all__ = ["IbkrTwsExecutionEventEmitter"]
