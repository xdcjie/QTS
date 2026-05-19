"""Shared execution report handling."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId
from qts.domain.orders import ExecutionReport, OrderFill
from qts.execution.order_manager import OrderManager
from qts.runtime.actor_ref import ActorRef


class ExecutionReportHandler:
    """Route normalized execution reports through order and account actors."""

    def __init__(
        self,
        *,
        order_manager: OrderManager,
        account_ref: ActorRef,
        multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None = None,
        account_id: AccountId | None = None,
        currency: str = "USD",
    ) -> None:
        """Create a report handler for an actor-owned order manager."""
        self._order_manager = order_manager
        self._account_ref = account_ref
        self._account_id = account_id
        self._multiplier_by_instrument = dict(multiplier_by_instrument or {})
        self._currency = currency
        self._quarantined_reports: list[ExecutionReport] = []

    @property
    def quarantined_reports(self) -> tuple[ExecutionReport, ...]:
        """Read-only collection of reports that could not be resolved to an order."""
        return tuple(self._quarantined_reports)

    def handle(self, report: ExecutionReport) -> tuple[OrderFill, ...]:
        """Apply a normalized execution report and enqueue account fill updates."""
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
        for fill in result.fills:
            from qts.runtime.actors.account_actor import ApplyFill

            self._account_ref.tell(
                ApplyFill(
                    fill=fill,
                    currency=self._currency,
                    multiplier=self._multiplier_by_instrument.get(fill.instrument_id, Decimal("1")),
                    fill_time=report.fill_time,
                )
            )
        return result.fills


__all__ = ["ExecutionReportHandler"]
