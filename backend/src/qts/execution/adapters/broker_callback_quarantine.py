"""Broker callback quarantine for unresolved provider callbacks."""

from __future__ import annotations

from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrAccountSummaryPayload,
    IbkrExecutionPayload,
    IbkrOpenOrderPayload,
    IbkrOrderStatusPayload,
    IbkrPositionPayload,
)


class BrokerCallbackQuarantine:
    """Owns unresolved broker callbacks until identity mapping can resolve them."""

    def __init__(self) -> None:
        self._executions: list[IbkrExecutionPayload] = []
        self._open_orders: list[IbkrOpenOrderPayload] = []
        self._order_statuses: list[IbkrOrderStatusPayload] = []
        self._positions: list[IbkrPositionPayload] = []
        self._account_summaries: list[IbkrAccountSummaryPayload] = []

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
    def positions(self) -> tuple[IbkrPositionPayload, ...]:
        """Return unresolved position callbacks."""

        return tuple(self._positions)

    @property
    def account_summaries(self) -> tuple[IbkrAccountSummaryPayload, ...]:
        """Return unresolved accountSummary callbacks."""

        return tuple(self._account_summaries)

    @property
    def has_unresolved(self) -> bool:
        """Return whether any unresolved callbacks remain."""

        return bool(
            self._executions
            or self._open_orders
            or self._order_statuses
            or self._positions
            or self._account_summaries
        )

    def add_execution(self, payload: IbkrExecutionPayload) -> None:
        """Quarantine an execution callback."""

        self._executions.append(payload)

    def replace_executions(self, payloads: list[IbkrExecutionPayload]) -> None:
        """Replace unresolved execution callbacks after a resolve attempt."""

        self._executions = payloads

    def replace_open_orders(self, payloads: list[IbkrOpenOrderPayload]) -> None:
        """Replace unresolved openOrder callbacks after a resolve attempt."""

        self._open_orders = payloads

    def replace_order_statuses(self, payloads: list[IbkrOrderStatusPayload]) -> None:
        """Replace unresolved orderStatus callbacks after a resolve attempt."""

        self._order_statuses = payloads

    def add_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Quarantine an openOrder callback."""

        self._open_orders.append(payload)

    def add_order_status(self, payload: IbkrOrderStatusPayload) -> None:
        """Quarantine an orderStatus callback."""

        self._order_statuses.append(payload)

    def add_position(self, payload: IbkrPositionPayload) -> None:
        """Quarantine a position callback."""

        self._positions.append(payload)

    def add_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Quarantine an accountSummary callback."""

        self._account_summaries.append(payload)


__all__ = ["BrokerCallbackQuarantine"]
