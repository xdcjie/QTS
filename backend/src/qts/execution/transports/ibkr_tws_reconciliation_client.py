"""IBKR TWS reconciliation request client."""

from __future__ import annotations

from typing import Any

from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrTwsOrderExecutionTransportConfig,
    _ibapi_attr,
)


class IbkrTwsReconciliationClient:
    """Owns broker state requests used during startup and reconnect reconciliation."""

    def __init__(self, *, config: IbkrTwsOrderExecutionTransportConfig) -> None:
        self._config = config
        self._request_sequence = 0

    def request_startup_reconciliation(self, app: Any) -> None:
        """Request broker state needed to reconcile after startup or reconnect."""

        app.reqOpenOrders()
        if self._config.request_all_open_orders_on_reconnect:
            app.reqAllOpenOrders()
        app.reqPositions()
        execution_filter_class = _ibapi_attr("ibapi.execution", "ExecutionFilter")
        app.reqExecutions(self._reserve_request_id(), execution_filter_class())
        app.reqAccountSummary(
            self._reserve_request_id(),
            "All",
            "NetLiquidation,TotalCashValue,AvailableFunds",
        )

    def _reserve_request_id(self) -> int:
        self._request_sequence += 1
        return self._request_sequence


__all__ = ["IbkrTwsReconciliationClient"]
