"""Shared execution report handling."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.execution.order_manager import ExecutionReport, OrderFill, OrderManager
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import ApplyFill


class ExecutionReportHandler:
    """Route normalized execution reports through order and account actors."""

    def __init__(
        self,
        *,
        order_manager: OrderManager,
        account_ref: ActorRef,
        multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None = None,
        currency: str = "USD",
    ) -> None:
        """Create a report handler for an actor-owned order manager."""
        self._order_manager = order_manager
        self._account_ref = account_ref
        self._multiplier_by_instrument = dict(multiplier_by_instrument or {})
        self._currency = currency

    def handle(self, report: ExecutionReport) -> tuple[OrderFill, ...]:
        """Apply a normalized execution report and enqueue account fill updates."""
        result = self._order_manager.process_report(report)
        for fill in result.fills:
            self._account_ref.tell(
                ApplyFill(
                    fill=fill,
                    currency=self._currency,
                    multiplier=self._multiplier_by_instrument.get(fill.instrument_id, Decimal("1")),
                )
            )
        return result.fills


__all__ = ["ExecutionReportHandler"]
