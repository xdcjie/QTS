"""Shared execution report handling."""

from __future__ import annotations

from qts.core.ids import AccountId
from qts.domain.orders import ExecutionReport, OrderFill
from qts.execution.order_manager import OrderManager


class ExecutionReportHandler:
    """Process normalized execution reports through the order manager.

    Returns validated fills for the owning actor to route downstream.
    Does NOT directly send messages to the account actor; the owning
    order manager actor is responsible for routing fill messages.
    """

    def __init__(
        self,
        *,
        order_manager: OrderManager,
        account_id: AccountId | None = None,
    ) -> None:
        """Create a report handler for an actor-owned order manager."""
        self._order_manager = order_manager
        self._account_id = account_id
        self._quarantined_reports: list[ExecutionReport] = []

    @property
    def quarantined_reports(self) -> tuple[ExecutionReport, ...]:
        """Read-only collection of reports that could not be resolved to an order."""
        return tuple(self._quarantined_reports)

    def handle(self, report: ExecutionReport) -> tuple[OrderFill, ...]:
        """Apply a normalized execution report and return validated fills.

        The caller is responsible for routing the returned fills to the
        account actor.
        """
        try:
            result = self._order_manager.process_report(report)
        except KeyError:
            self._quarantined_reports.append(report)
            return ()
        if self._account_id is not None:
            for fill in result.fills:
                if fill.account_id != self._account_id:
                    self._quarantined_reports.append(report)
                    return ()
        return result.fills


__all__ = ["ExecutionReportHandler"]
