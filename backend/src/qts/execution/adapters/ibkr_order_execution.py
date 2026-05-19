"""IBKR order execution adapter facade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from qts.core.ids import AccountId, BrokerId, OrderId, StrategyId
from qts.domain.orders import ExecutionReport, OrderIntent, OrderType, TimeInForce
from qts.execution.adapters.ibkr_callback_normalizer import (
    IbkrCallbackNormalizer,
    IbkrExecutionReport,
    IbkrOrderCallbackEvent,
)
from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
from qts.execution.adapters.ibkr_order_request_mapper import IbkrOrderRequestMapper
from qts.execution.broker import BrokerCapabilities, BrokerCommissionReport
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrAccountSummaryPayload,
    IbkrCommissionPayload,
    IbkrConnectionEvent,
    IbkrConnectionEventPayload,
    IbkrErrorPayload,
    IbkrExecutionPayload,
    IbkrOpenOrderPayload,
    IbkrOrderContractSpec,
    IbkrOrderRequest,
    IbkrOrderStatusPayload,
    IbkrPositionPayload,
    IbkrTransportError,
)
from qts.reconciliation.snapshots import ReconciliationSnapshot
from qts.registry.broker_symbol_mapping import BrokerSymbolMapping


@dataclass(frozen=True, slots=True)
class IbkrOrderExecutionConnection:
    """IBKR order execution connection settings."""

    host: str
    port: int
    client_id: int
    broker_id: BrokerId
    account_id: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")


class IbkrOrderExecutionAdapter:
    """Public facade for IBKR order request mapping and callback normalization."""

    def __init__(
        self,
        *,
        connection: IbkrOrderExecutionConnection,
        symbol_mapping: BrokerSymbolMapping,
        capabilities: BrokerCapabilities | None = None,
        order_map: BrokerOrderMap | None = None,
        live_capital_decision: object | None = None,
    ) -> None:
        """Perform __init__."""
        self.connection = connection
        self._order_map = order_map
        self._live_capital_decision = live_capital_decision
        self._capabilities = capabilities or BrokerCapabilities(
            broker_id=connection.broker_id,
            supports_market_orders=True,
            supports_limit_orders=True,
            supports_cancel=True,
            supports_replace=False,
            supports_fractional=False,
            supports_short=False,
        )
        self._request_mapper = IbkrOrderRequestMapper(
            account_id=connection.account_id,
            symbol_mapping=symbol_mapping,
            capabilities=self._capabilities,
        )
        self._callback_normalizer = IbkrCallbackNormalizer(
            account_id=connection.account_id,
            symbol_mapping=symbol_mapping,
            order_map=order_map,
        )

    @property
    def quarantined_executions(self) -> tuple[IbkrExecutionPayload, ...]:
        """Read-only unresolved IBKR execution callbacks."""
        return self._callback_normalizer.quarantined_executions

    @property
    def quarantined_open_orders(self) -> tuple[IbkrOpenOrderPayload, ...]:
        """Read-only unresolved IBKR openOrder callbacks."""
        return self._callback_normalizer.quarantined_open_orders

    @property
    def quarantined_order_statuses(self) -> tuple[IbkrOrderStatusPayload, ...]:
        """Read-only unresolved IBKR order-status callbacks."""
        return self._callback_normalizer.quarantined_order_statuses

    @property
    def quarantined_positions(self) -> tuple[IbkrPositionPayload, ...]:
        """Read-only unresolved IBKR position callbacks."""
        return self._callback_normalizer.quarantined_positions

    @property
    def quarantined_account_summaries(self) -> tuple[IbkrAccountSummaryPayload, ...]:
        """Read-only unresolved IBKR account-summary callbacks."""
        return self._callback_normalizer.quarantined_account_summaries

    @property
    def callback_events(self) -> tuple[IbkrOrderCallbackEvent, ...]:
        """Read-only IBKR callback audit events."""
        return self._callback_normalizer.callback_events

    @property
    def has_unresolved_callbacks(self) -> bool:
        """Return whether unresolved IBKR callbacks remain quarantined."""

        return self._callback_normalizer.has_unresolved_callbacks

    def to_order_request(
        self,
        intent: OrderIntent,
        *,
        client_order_id: str,
        strategy_id: StrategyId | None = None,
        order_type: OrderType | None = None,
        time_in_force: TimeInForce | None = None,
        limit_price: Decimal | None = None,
        asset_class: str = "equity",
        opens_short: bool = False,
        contract: IbkrOrderContractSpec | None = None,
        outside_regular_trading_hours: bool = False,
        what_if: bool = False,
    ) -> IbkrOrderRequest:
        """Map an internal order intent to an IBKR order request."""

        self._assert_live_capital_order_allowed()
        self.validate_no_unresolved_callbacks()
        return self._request_mapper.to_order_request(
            intent,
            client_order_id=client_order_id,
            strategy_id=strategy_id,
            order_type=order_type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            asset_class=asset_class,
            opens_short=opens_short,
            contract=contract,
            outside_regular_trading_hours=outside_regular_trading_hours,
            what_if=what_if,
        )

    def _assert_live_capital_order_allowed(self) -> None:
        gate = self._live_capital_decision
        if gate is None:
            return
        cast(Any, gate).assert_live_order_allowed()

    def record_submitted_order(
        self,
        request: IbkrOrderRequest,
        *,
        ibkr_order_id: str,
        submitted_at: datetime | None = None,
    ) -> None:
        """Record a submitted IBKR order id for callback reconciliation."""
        if self._order_map is None:
            return
        if request.internal_account_id is None:
            raise ValueError("internal_account_id is required to record IBKR order mapping")
        submitted_at = submitted_at or datetime.now(UTC)
        self._order_map.record_pending_submission(
            internal_order_id=request.internal_order_id,
            client_order_id=request.client_order_id,
            account_id=request.internal_account_id,
            strategy_id=request.strategy_id,
            submitted_at=submitted_at,
        )
        self._order_map.attach_ibkr_order_id(
            client_order_id=request.client_order_id,
            ibkr_order_id=ibkr_order_id,
        )

    def resolve_cancel_broker_order_id(
        self,
        *,
        internal_order_id: OrderId,
        client_order_id: str,
    ) -> str:
        """Resolve the IBKR order id for a cancel request through route metadata."""
        self.validate_cancel_supported()
        if not client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        if self._order_map is None:
            raise RuntimeError("BrokerOrderMap is required to resolve IBKR cancel order id")
        record = self._order_map.by_internal_order_id(internal_order_id)
        if record.client_order_id != client_order_id:
            raise ValueError("client_order_id does not match internal_order_id route")
        if record.ibkr_order_id is None:
            raise RuntimeError("IBKR order id is not known for cancel request")
        return record.ibkr_order_id

    def normalize_execution_report(self, report: IbkrExecutionReport) -> ExecutionReport:
        """Normalize an IBKR execution report to the internal execution report."""

        return self._callback_normalizer.normalize_execution_report(report)

    def on_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Normalize a raw IBKR order-status callback."""

        return self._callback_normalizer.on_order_status(payload)

    def on_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Record an IBKR openOrder callback against the broker-order map."""

        self._callback_normalizer.on_open_order(payload)

    def on_position(self, payload: IbkrPositionPayload) -> None:
        """Record an IBKR position callback for broker reconciliation."""

        self._callback_normalizer.on_position(payload)

    def on_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Record an IBKR account summary callback for broker reconciliation."""

        self._callback_normalizer.on_account_summary(payload)

    def broker_reconciliation_snapshot(
        self,
        *,
        account_id: AccountId,
    ) -> ReconciliationSnapshot:
        """Return the latest normalized broker-side snapshot for reconciliation."""

        return self._callback_normalizer.broker_reconciliation_snapshot(account_id=account_id)

    def on_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Stage a raw IBKR execution callback until its commission arrives."""

        return self._callback_normalizer.on_execution(payload)

    def on_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | BrokerCommissionReport:
        """Normalize a raw IBKR commission callback and complete matching fills."""

        return self._callback_normalizer.on_commission(payload)

    def resolve_quarantined_callbacks(self) -> tuple[ExecutionReport, ...]:
        """Try to resolve quarantined callbacks after order mapping changes."""

        return self._callback_normalizer.resolve_quarantined_callbacks()

    def on_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        """Normalize a raw IBKR error callback."""

        return IbkrTransportError(
            request_id=payload.request_id,
            code=payload.code,
            message=payload.message,
        )

    def on_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Normalize a raw IBKR disconnect callback."""

        return IbkrConnectionEvent(kind="disconnect", reason=payload.reason)

    def on_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Normalize a raw IBKR reconnect callback."""

        return IbkrConnectionEvent(kind="reconnect", reason=payload.reason)

    def validate_cancel_supported(self) -> None:
        """Validate cancel support before sending an IBKR cancel request."""

        if not self._capabilities.supports_cancel:
            raise ValueError("cancel is not supported by broker capabilities")

    def validate_replace_supported(self) -> None:
        """Validate replace support before sending an IBKR replace request."""

        if not self._capabilities.supports_replace:
            raise ValueError("replace is not supported by broker capabilities")

    def validate_no_unresolved_callbacks(self) -> None:
        """Fail closed while broker callbacks remain unresolved."""

        self._callback_normalizer.validate_no_unresolved_callbacks()


__all__ = [
    "IbkrExecutionReport",
    "IbkrOrderCallbackEvent",
    "IbkrOrderExecutionAdapter",
    "IbkrOrderExecutionConnection",
    "IbkrOrderContractSpec",
    "IbkrOrderRequest",
]
