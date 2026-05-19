"""IBKR position and account-summary callback recording."""

from __future__ import annotations

from qts.domain.orders import ExecutionReport
from qts.execution.adapters.broker_callback_quarantine import BrokerCallbackQuarantine
from qts.execution.adapters.ibkr_callback_types import (
    IbkrOrderCallbackEvent,
    record_account_mismatch_event,
)
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrAccountSummaryPayload,
    IbkrPositionPayload,
)
from qts.reconciliation.snapshots import (
    ReconciliationCashSnapshot,
    ReconciliationPositionSnapshot,
)
from qts.registry.broker_symbol_mapping import BrokerSymbolMapping


class IbkrPositionRecorder:
    """Owns IBKR position and cash recording for broker reconciliation snapshots."""

    def __init__(
        self,
        *,
        account_id: str,
        symbol_mapping: BrokerSymbolMapping,
        callback_events: list[IbkrOrderCallbackEvent],
        callback_quarantine: BrokerCallbackQuarantine,
    ) -> None:
        self._account_id = account_id
        self._symbol_mapping = symbol_mapping
        self._callback_events = callback_events
        self._callback_quarantine = callback_quarantine
        self._broker_positions: dict[str, ReconciliationPositionSnapshot] = {}
        self._broker_cash: dict[str, ReconciliationCashSnapshot] = {}

    @property
    def broker_positions(self) -> dict[str, ReconciliationPositionSnapshot]:
        """Read-only access to recorded broker positions."""
        return self._broker_positions

    @property
    def broker_cash(self) -> dict[str, ReconciliationCashSnapshot]:
        """Read-only access to recorded broker cash balances."""
        return self._broker_cash

    def on_position(self, payload: IbkrPositionPayload) -> None:
        """Record an IBKR position callback for broker reconciliation."""

        if payload.account_id != self._account_id:
            self._callback_quarantine.add_position(payload)
            record_account_mismatch_event(
                self._callback_events,
                self._account_id,
                report_id=None,
                broker_order_id=None,
                observed_account=payload.account_id,
            )
            return
        instrument_id = self._symbol_mapping.to_instrument_id(payload.broker_symbol)
        self._broker_positions[instrument_id.value] = ReconciliationPositionSnapshot(
            instrument_id=instrument_id,
            quantity=payload.quantity,
        )

    def on_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Record an IBKR account summary callback for broker reconciliation."""

        if payload.account_id != self._account_id:
            self._callback_quarantine.add_account_summary(payload)
            record_account_mismatch_event(
                self._callback_events,
                self._account_id,
                report_id=None,
                broker_order_id=None,
                observed_account=payload.account_id,
            )
            return
        if payload.tag != "TotalCashValue":
            return
        self._broker_cash[payload.currency] = ReconciliationCashSnapshot(
            currency=payload.currency,
            balance=payload.value,
        )

    def resolve_quarantined(self) -> tuple[ExecutionReport, ...]:
        """Position/account-summary callbacks do not resolve to execution reports."""
        return ()


__all__ = ["IbkrPositionRecorder"]
