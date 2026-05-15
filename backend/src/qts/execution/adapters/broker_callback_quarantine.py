"""Broker callback quarantine for unresolved provider callbacks."""

from __future__ import annotations

from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrExecutionPayload,
    IbkrOpenOrderPayload,
    IbkrOrderStatusPayload,
)


class BrokerCallbackQuarantine:
    """Owns unresolved broker callbacks until identity mapping can resolve them."""

    def __init__(self) -> None:
        self._executions: list[IbkrExecutionPayload] = []
        self._open_orders: list[IbkrOpenOrderPayload] = []
        self._order_statuses: list[IbkrOrderStatusPayload] = []

    @property
    def executions(self) -> tuple[IbkrExecutionPayload, ...]:
        """Return unresolved execution callbacks."""

        return tuple(self._executions)

    @property
    def open_orders(self) -> tuple[IbkrOpenOrderPayload, ...]:
        """Return unresolved openOrder callbacks."""

        return tuple(self._open_orders)

    @property
    def order_statuses(self) -> tuple[IbkrOrderStatusPayload, ...]:
        """Return unresolved orderStatus callbacks."""

        return tuple(self._order_statuses)

    @property
    def has_unresolved(self) -> bool:
        """Return whether any unresolved callbacks remain."""

        return bool(self._executions or self._open_orders or self._order_statuses)

    def add_execution(self, payload: IbkrExecutionPayload) -> None:
        """Quarantine an execution callback."""

        self._executions.append(payload)

    def replace_executions(self, payloads: list[IbkrExecutionPayload]) -> None:
        """Replace unresolved execution callbacks after a resolve attempt."""

        self._executions = payloads

    def add_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Quarantine an openOrder callback."""

        self._open_orders.append(payload)

    def add_order_status(self, payload: IbkrOrderStatusPayload) -> None:
        """Quarantine an orderStatus callback."""

        self._order_statuses.append(payload)


__all__ = ["BrokerCallbackQuarantine"]
