"""IBKR TWS order submit/cancel client."""

from __future__ import annotations

from typing import Any

from qts.execution.transports.ibkr_order_ids import IbkrOrderIdAllocator
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrOrderExecutionCallbackSink,
    IbkrOrderRequest,
    IbkrTwsOrderExecutionTransportConfig,
    _ibapi_attr,
)


class IbkrTwsOrderClient:
    """Owns IBKR order id reservation plus submit and cancel calls."""

    def __init__(
        self,
        *,
        config: IbkrTwsOrderExecutionTransportConfig,
        sink: IbkrOrderExecutionCallbackSink,
        order_id_allocator: IbkrOrderIdAllocator | None = None,
    ) -> None:
        self._config = config
        self._sink = sink
        self._order_id_allocator = order_id_allocator or IbkrOrderIdAllocator(
            config.order_id_store_path
        )
        self._submitted_requests: dict[str, IbkrOrderRequest] = {}

    def submit_order_with_broker_id(self, app: Any, request: IbkrOrderRequest) -> str:
        """Submit an IBKR order request and return the broker order id."""

        broker_order_id = str(self._reserve_order_id())
        self._submitted_requests[broker_order_id] = request
        app.placeOrder(
            int(broker_order_id),
            request.to_ibapi_contract(),
            request.to_ibapi_order(),
        )
        self._sink.record_submitted_order(request, ibkr_order_id=broker_order_id)
        return broker_order_id

    def cancel_order(self, app: Any, broker_order_id: str) -> None:
        """Cancel a broker order by broker order id."""

        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        order_cancel_class = _ibapi_attr("ibapi.order_cancel", "OrderCancel")
        app.cancelOrder(int(broker_order_id), order_cancel_class())

    def mark_next_order_id(self, order_id: int) -> None:
        """Record the next valid IBKR order id."""

        if order_id <= 0:
            raise ValueError("order_id must be positive")
        self._order_id_allocator.reconcile_next_valid_id(
            client_id=self._config.client_id,
            broker_next_valid_id=order_id,
        )

    def _reserve_order_id(self) -> int:
        if self._order_id_allocator.next_id(client_id=self._config.client_id) is None:
            raise RuntimeError("IBKR order-execution transport has no next order id")
        return self._order_id_allocator.allocate(client_id=self._config.client_id)


__all__ = ["IbkrTwsOrderClient"]
