"""IBKR order execution adapter skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from qts.core.ids import AccountId, BrokerId, OrderId, StrategyId
from qts.domain.orders import ExecutionReport, OrderIntent, OrderSide
from qts.execution.adapters.broker_callback_quarantine import BrokerCallbackQuarantine
from qts.execution.adapters.ibkr_order_map import BrokerOrderMap
from qts.execution.broker import (
    BrokerCapabilities,
    BrokerExecutionReportStatus,
    BrokerOrderType,
    TimeInForce,
    normalize_broker_status,
)
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrAccountSummaryPayload,
    IbkrCommissionPayload,
    IbkrCommissionReport,
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
from qts.reconciliation.snapshots import (
    CashSnapshot,
    OrderSnapshot,
    PositionSnapshot,
    ReconciliationSnapshot,
)
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


@dataclass(frozen=True, slots=True)
class IbkrExecutionReport:
    """IBKR execution report shape before normalization."""

    report_id: str
    broker_order_id: str
    status: BrokerExecutionReportStatus
    filled_quantity: Decimal = Decimal("0")
    fill_price: Decimal | None = None
    fill_id: str | None = None
    commission: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class IbkrOrderCallbackEvent:
    """Audit event for normalized IBKR order callback handling."""

    kind: str
    report_id: str | None = None
    broker_order_id: str | None = None
    execution_id: str | None = None
    reason: str | None = None
    expected_account: str | None = None
    observed_account: str | None = None

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("kind must not be empty")
        for field_name, value in (
            ("report_id", self.report_id),
            ("broker_order_id", self.broker_order_id),
            ("execution_id", self.execution_id),
            ("reason", self.reason),
            ("expected_account", self.expected_account),
            ("observed_account", self.observed_account),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be empty when provided")


class IbkrOrderExecutionAdapter:
    """Maps internal orders to IBKR order requests and normalizes reports."""

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
        self._symbol_mapping = symbol_mapping
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
        self._pending_executions: dict[tuple[str, str, str], IbkrExecutionPayload] = {}
        self._commissions: dict[str, IbkrCommissionPayload] = {}
        self._completed_execution_keys: set[tuple[str, str, str]] = set()
        self._seen_order_status_keys: set[tuple[str, str, str | None]] = set()
        self._seen_open_order_keys: set[
            tuple[str, str | None, str | None, str | None, str | None, str | None, Decimal | None]
        ] = set()
        self._callback_quarantine = BrokerCallbackQuarantine()
        self._callback_events: list[IbkrOrderCallbackEvent] = []
        self._broker_open_orders: dict[OrderId, OrderSnapshot] = {}
        self._broker_positions: dict[str, PositionSnapshot] = {}
        self._broker_cash: dict[str, CashSnapshot] = {}

    @property
    def quarantined_executions(self) -> tuple[IbkrExecutionPayload, ...]:
        """Read-only unresolved IBKR execution callbacks."""
        return self._callback_quarantine.executions

    @property
    def quarantined_open_orders(self) -> tuple[IbkrOpenOrderPayload, ...]:
        """Read-only unresolved IBKR openOrder callbacks."""
        return self._callback_quarantine.open_orders

    @property
    def quarantined_order_statuses(self) -> tuple[IbkrOrderStatusPayload, ...]:
        """Read-only unresolved IBKR order-status callbacks."""
        return self._callback_quarantine.order_statuses

    @property
    def quarantined_positions(self) -> tuple[IbkrPositionPayload, ...]:
        """Read-only unresolved IBKR position callbacks."""
        return self._callback_quarantine.positions

    @property
    def quarantined_account_summaries(self) -> tuple[IbkrAccountSummaryPayload, ...]:
        """Read-only unresolved IBKR account-summary callbacks."""
        return self._callback_quarantine.account_summaries

    @property
    def callback_events(self) -> tuple[IbkrOrderCallbackEvent, ...]:
        """Read-only IBKR callback audit events."""
        return tuple(self._callback_events)

    @property
    def has_unresolved_callbacks(self) -> bool:
        """Return whether unresolved IBKR callbacks remain quarantined."""

        return self._callback_quarantine.has_unresolved

    def to_order_request(
        self,
        intent: OrderIntent,
        *,
        client_order_id: str,
        strategy_id: StrategyId | None = None,
        order_type: BrokerOrderType | None = None,
        time_in_force: TimeInForce | None = None,
        limit_price: Decimal | None = None,
        asset_class: str = "equity",
        opens_short: bool = False,
        contract: IbkrOrderContractSpec | None = None,
        outside_regular_trading_hours: bool = False,
        what_if: bool = False,
    ) -> IbkrOrderRequest:
        """Perform to_order_request."""
        if not client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        spec = intent.order_spec
        resolved_order_type = order_type or spec.order_type
        resolved_time_in_force = time_in_force or spec.time_in_force
        resolved_limit_price = limit_price if limit_price is not None else spec.limit_price
        self._assert_live_capital_order_allowed()
        self.validate_no_unresolved_callbacks()
        self._validate_order_request(
            intent,
            order_type=resolved_order_type,
            time_in_force=resolved_time_in_force,
            limit_price=resolved_limit_price,
            asset_class=asset_class,
            opens_short=opens_short,
        )
        return IbkrOrderRequest(
            internal_order_id=intent.order_id,
            client_order_id=client_order_id,
            internal_account_id=intent.account_id,
            strategy_id=strategy_id,
            account_id=self.connection.account_id,
            broker_symbol=self._symbol_mapping.to_broker_symbol(intent.instrument_id),
            side=intent.side.value,
            quantity=intent.quantity,
            order_type=resolved_order_type,
            time_in_force=resolved_time_in_force,
            limit_price=resolved_limit_price,
            bracket_legs=None if spec.bracket is None else spec.bracket.legs,
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
        """Perform normalize_execution_report."""
        return ExecutionReport(
            report_id=report.report_id,
            broker_order_id=report.broker_order_id,
            status=normalize_broker_status(report.status),
            filled_quantity=report.filled_quantity,
            fill_price=report.fill_price,
            fill_id=report.fill_id,
            commission=report.commission,
        )

    def on_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Normalize a raw IBKR order-status callback."""

        self._record_callback_event(
            "ibkr_order_status_received",
            report_id=payload.report_id,
            broker_order_id=payload.broker_order_id,
        )
        status_key = (payload.broker_order_id, payload.status, payload.perm_id)
        if status_key in self._seen_order_status_keys:
            self._record_callback_event(
                "ibkr_order_callback_duplicate_dropped",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                reason="order_status_already_seen",
            )
            return None
        if self._order_map is not None:
            try:
                if payload.perm_id is not None:
                    self._order_map.attach_perm_id(
                        ibkr_order_id=payload.broker_order_id,
                        perm_id=payload.perm_id,
                    )
                record = self._order_map.by_ibkr_order_id(payload.broker_order_id)
                if self._is_late_cancel_after_fill(
                    current_status=record.status,
                    next_status=payload.status,
                ):
                    self._record_callback_event(
                        "ibkr_order_callback_late_terminal_dropped",
                        report_id=payload.report_id,
                        broker_order_id=payload.broker_order_id,
                        reason="late_cancel_after_filled",
                    )
                    return None
                self._order_map.mark_status(
                    ibkr_order_id=payload.broker_order_id,
                    status=payload.status,
                    last_broker_status_at=datetime.now(UTC),
                )
            except KeyError:
                self._callback_quarantine.add_order_status(payload)
                self._record_callback_event(
                    "ibkr_order_callback_unresolved_quarantined",
                    report_id=payload.report_id,
                    broker_order_id=payload.broker_order_id,
                    reason="unknown_ibkr_order_id",
                )
                return None
        self._seen_order_status_keys.add(status_key)
        return self.normalize_execution_report(
            IbkrExecutionReport(
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                status=self._status_from_ibkr(payload.status),
            )
        )

    def on_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Record an IBKR openOrder callback against the broker-order map."""

        self._record_callback_event(
            "ibkr_open_order_received",
            report_id=payload.report_id,
            broker_order_id=payload.broker_order_id,
        )
        if self._order_map is None:
            return
        if payload.client_order_id is None:
            self._callback_quarantine.add_open_order(payload)
            self._record_callback_event(
                "ibkr_order_callback_unresolved_quarantined",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                reason="missing_client_order_id",
            )
            return
        try:
            open_order_key = self._open_order_key(payload)
            if open_order_key in self._seen_open_order_keys:
                self._record_callback_event(
                    "ibkr_order_callback_duplicate_dropped",
                    report_id=payload.report_id,
                    broker_order_id=payload.broker_order_id,
                    reason="open_order_already_seen",
                )
                return
            record = self._order_map.by_client_order_id(payload.client_order_id)
            self._order_map.attach_ibkr_order_id(
                client_order_id=payload.client_order_id,
                ibkr_order_id=payload.broker_order_id,
            )
            if payload.perm_id is not None:
                self._order_map.attach_perm_id(
                    ibkr_order_id=payload.broker_order_id,
                    perm_id=payload.perm_id,
                )
            if payload.status is not None:
                self._order_map.mark_status(
                    ibkr_order_id=payload.broker_order_id,
                    status=payload.status,
                    last_broker_status_at=datetime.now(UTC),
                )
            if (
                payload.broker_symbol is not None
                and payload.side is not None
                and payload.quantity is not None
                and payload.status is not None
            ):
                self._broker_open_orders[record.internal_order_id] = OrderSnapshot(
                    order_id=record.internal_order_id,
                    instrument_id=self._symbol_mapping.to_instrument_id(payload.broker_symbol),
                    side=self._order_side_from_ibkr(payload.side),
                    quantity=payload.quantity,
                    status=payload.status,
                )
            self._seen_open_order_keys.add(open_order_key)
        except KeyError:
            self._callback_quarantine.add_open_order(payload)
            self._record_callback_event(
                "ibkr_order_callback_unresolved_quarantined",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                reason="unknown_client_order_id",
            )

    def on_position(self, payload: IbkrPositionPayload) -> None:
        """Record an IBKR position callback for broker reconciliation."""

        if payload.account_id != self.connection.account_id:
            self._callback_quarantine.add_position(payload)
            self._record_account_mismatch_event(
                report_id=None,
                broker_order_id=None,
                observed_account=payload.account_id,
            )
            return
        instrument_id = self._symbol_mapping.to_instrument_id(payload.broker_symbol)
        self._broker_positions[instrument_id.value] = PositionSnapshot(
            instrument_id=instrument_id,
            quantity=payload.quantity,
        )

    def on_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Record an IBKR account summary callback for broker reconciliation."""

        if payload.account_id != self.connection.account_id:
            self._callback_quarantine.add_account_summary(payload)
            self._record_account_mismatch_event(
                report_id=None,
                broker_order_id=None,
                observed_account=payload.account_id,
            )
            return
        if payload.tag != "TotalCashValue":
            return
        self._broker_cash[payload.currency] = CashSnapshot(
            currency=payload.currency,
            balance=payload.value,
        )

    def broker_reconciliation_snapshot(
        self,
        *,
        account_id: AccountId,
    ) -> ReconciliationSnapshot:
        """Return the latest normalized broker-side snapshot for reconciliation."""

        return ReconciliationSnapshot(
            account_id=account_id,
            orders=tuple(
                self._broker_open_orders[order_id]
                for order_id in sorted(self._broker_open_orders, key=lambda item: item.value)
            ),
            positions=tuple(
                self._broker_positions[instrument_id]
                for instrument_id in sorted(self._broker_positions)
            ),
            cash=tuple(self._broker_cash[currency] for currency in sorted(self._broker_cash)),
        )

    def on_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Stage a raw IBKR execution callback until its commission arrives."""

        self._record_callback_event(
            "ibkr_execution_details_received",
            report_id=payload.report_id,
            broker_order_id=payload.broker_order_id,
            execution_id=payload.execution_id,
        )
        if payload.account_id is not None and payload.account_id != self.connection.account_id:
            self._callback_quarantine.add_execution(payload)
            self._record_account_mismatch_event(
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                execution_id=payload.execution_id,
                observed_account=payload.account_id,
            )
            return None
        execution_key = self._execution_key(payload)
        if execution_key in self._completed_execution_keys:
            self._record_callback_event(
                "ibkr_order_callback_duplicate_dropped",
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                execution_id=payload.execution_id,
                reason="execution_already_completed",
            )
            return None
        if self._order_map is not None:
            try:
                self._order_map.by_ibkr_order_id(payload.broker_order_id)
            except KeyError:
                self._callback_quarantine.add_execution(payload)
                self._record_callback_event(
                    "ibkr_order_callback_unresolved_quarantined",
                    report_id=payload.report_id,
                    broker_order_id=payload.broker_order_id,
                    execution_id=payload.execution_id,
                    reason="unknown_ibkr_order_id",
                )
                return None
        self._pending_executions[execution_key] = payload
        commission = self._commissions.get(payload.execution_id)
        if commission is None:
            return None
        return self._pop_commissioned_execution(execution_key)

    def on_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Normalize a raw IBKR commission callback and complete matching fills."""

        self._record_callback_event(
            "ibkr_commission_report_received",
            execution_id=payload.execution_id,
        )
        self._commissions[payload.execution_id] = payload
        report = self._pop_commissioned_execution_by_execution_id(payload.execution_id)
        if report is not None:
            return report
        if any(key[2] == payload.execution_id for key in self._completed_execution_keys):
            self._record_callback_event(
                "ibkr_order_callback_duplicate_dropped",
                execution_id=payload.execution_id,
                reason="commission_for_completed_execution",
            )
            return IbkrCommissionReport(
                execution_id=payload.execution_id,
                commission=payload.commission,
                currency=payload.currency,
            )
        return IbkrCommissionReport(
            execution_id=payload.execution_id,
            commission=payload.commission,
            currency=payload.currency,
        )

    def resolve_quarantined_callbacks(self) -> tuple[ExecutionReport, ...]:
        """Try to resolve quarantined callbacks after order mapping changes."""

        resolved_reports: list[ExecutionReport] = []
        unresolved_open_orders: list[IbkrOpenOrderPayload] = []
        for open_order_payload in self._callback_quarantine.open_orders:
            before_count = len(self._callback_quarantine.open_orders)
            self.on_open_order(open_order_payload)
            if len(self._callback_quarantine.open_orders) > before_count:
                self._callback_quarantine.replace_open_orders(
                    list(self._callback_quarantine.open_orders[:-1])
                )
                unresolved_open_orders.append(open_order_payload)
        self._callback_quarantine.replace_open_orders(unresolved_open_orders)

        unresolved_order_statuses: list[IbkrOrderStatusPayload] = []
        for order_status_payload in self._callback_quarantine.order_statuses:
            before_count = len(self._callback_quarantine.order_statuses)
            report = self.on_order_status(order_status_payload)
            if report is not None:
                resolved_reports.append(report)
            if len(self._callback_quarantine.order_statuses) > before_count:
                self._callback_quarantine.replace_order_statuses(
                    list(self._callback_quarantine.order_statuses[:-1])
                )
                unresolved_order_statuses.append(order_status_payload)
        self._callback_quarantine.replace_order_statuses(unresolved_order_statuses)

        unresolved_executions: list[IbkrExecutionPayload] = []
        for execution_payload in self._callback_quarantine.executions:
            if (
                execution_payload.account_id is not None
                and execution_payload.account_id != self.connection.account_id
            ):
                unresolved_executions.append(execution_payload)
                continue
            if self._order_map is not None:
                try:
                    self._order_map.by_ibkr_order_id(execution_payload.broker_order_id)
                except KeyError:
                    unresolved_executions.append(execution_payload)
                    continue
            execution_key = self._execution_key(execution_payload)
            if execution_key in self._completed_execution_keys:
                continue
            self._pending_executions[execution_key] = execution_payload
            report = self._pop_commissioned_execution(execution_key)
            if report is not None:
                resolved_reports.append(report)
            self._record_callback_event(
                "ibkr_order_callback_quarantine_resolved",
                report_id=execution_payload.report_id,
                broker_order_id=execution_payload.broker_order_id,
                execution_id=execution_payload.execution_id,
            )
        self._callback_quarantine.replace_executions(unresolved_executions)
        return tuple(resolved_reports)

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

    @staticmethod
    def _status_from_ibkr(status: str) -> BrokerExecutionReportStatus:
        normalized = status.strip().lower()
        status_map = {
            "apicancelled": BrokerExecutionReportStatus.CANCELLED,
            "cancelled": BrokerExecutionReportStatus.CANCELLED,
            "filled": BrokerExecutionReportStatus.FILLED,
            "inactive": BrokerExecutionReportStatus.REJECTED,
            "pendingcancel": BrokerExecutionReportStatus.ACCEPTED,
            "pendingsubmit": BrokerExecutionReportStatus.ACCEPTED,
            "presubmitted": BrokerExecutionReportStatus.ACCEPTED,
            "submitted": BrokerExecutionReportStatus.ACCEPTED,
        }
        try:
            return status_map[normalized]
        except KeyError as exc:
            raise ValueError(f"unsupported IBKR order status: {status}") from exc

    @staticmethod
    def _order_side_from_ibkr(side: str) -> OrderSide:
        normalized = side.strip().lower()
        if normalized in {"buy", "bot"}:
            return OrderSide.BUY
        if normalized in {"sell", "sld"}:
            return OrderSide.SELL
        raise ValueError(f"unsupported IBKR order side: {side}")

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

        if self.has_unresolved_callbacks:
            raise RuntimeError("unresolved IBKR callbacks require reconciliation before new orders")

    def _validate_order_request(
        self,
        intent: OrderIntent,
        *,
        order_type: BrokerOrderType,
        time_in_force: TimeInForce,
        limit_price: Decimal | None,
        asset_class: str,
        opens_short: bool,
    ) -> None:
        if not self._capabilities.supports_order_type(order_type):
            raise ValueError(f"order type is not supported: {order_type.value}")
        if not self._capabilities.supports_tif(time_in_force):
            raise ValueError(f"time in force is not supported: {time_in_force.value}")
        if not self._capabilities.supports_asset_class(asset_class):
            raise ValueError(f"asset class is not supported: {asset_class}")
        if order_type is BrokerOrderType.LIMIT and limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if (
            order_type not in {BrokerOrderType.LIMIT, BrokerOrderType.BRACKET}
            and limit_price is not None
        ):
            raise ValueError("limit_price is only valid for limit orders")
        if (
            not self._capabilities.supports_fractional
            and intent.quantity != intent.quantity.to_integral_value()
        ):
            raise ValueError("fractional quantity is not supported")
        self._capabilities.validate_order_quantity(intent.quantity)
        if opens_short and not self._capabilities.supports_short:
            raise ValueError("short orders are not supported")

    def _execution_key(self, payload: IbkrExecutionPayload) -> tuple[str, str, str]:
        account_id = payload.account_id or self.connection.account_id
        return (account_id, payload.broker_order_id, payload.execution_id)

    @staticmethod
    def _open_order_key(
        payload: IbkrOpenOrderPayload,
    ) -> tuple[str, str | None, str | None, str | None, str | None, str | None, Decimal | None]:
        return (
            payload.broker_order_id,
            payload.client_order_id,
            payload.perm_id,
            payload.status,
            payload.broker_symbol,
            payload.side,
            payload.quantity,
        )

    @staticmethod
    def _is_late_cancel_after_fill(*, current_status: str, next_status: str) -> bool:
        return current_status.strip().lower() == "filled" and next_status.strip().lower() in {
            "apicancelled",
            "cancelled",
        }

    def _pop_commissioned_execution_by_execution_id(
        self,
        execution_id: str,
    ) -> ExecutionReport | None:
        for execution_key in tuple(self._pending_executions):
            if execution_key[2] == execution_id:
                return self._pop_commissioned_execution(execution_key)
        return None

    def _pop_commissioned_execution(
        self,
        execution_key: tuple[str, str, str],
    ) -> ExecutionReport | None:
        execution = self._pending_executions.get(execution_key)
        commission = self._commissions.get(execution_key[2])
        if execution is None or commission is None:
            return None
        self._pending_executions.pop(execution_key)
        self._commissions.pop(execution_key[2])
        self._completed_execution_keys.add(execution_key)
        return self.normalize_execution_report(
            IbkrExecutionReport(
                report_id=execution.report_id,
                broker_order_id=execution.broker_order_id,
                status=BrokerExecutionReportStatus.FILLED,
                filled_quantity=execution.filled_quantity,
                fill_price=execution.fill_price,
                fill_id=execution.execution_id,
                commission=commission.commission,
            )
        )

    def _record_callback_event(
        self,
        kind: str,
        *,
        report_id: str | None = None,
        broker_order_id: str | None = None,
        execution_id: str | None = None,
        reason: str | None = None,
        expected_account: str | None = None,
        observed_account: str | None = None,
    ) -> None:
        self._callback_events.append(
            IbkrOrderCallbackEvent(
                kind=kind,
                report_id=report_id,
                broker_order_id=broker_order_id,
                execution_id=execution_id,
                reason=reason,
                expected_account=expected_account,
                observed_account=observed_account,
            )
        )

    def _record_account_mismatch_event(
        self,
        *,
        report_id: str | None,
        broker_order_id: str | None,
        observed_account: str,
        execution_id: str | None = None,
    ) -> None:
        self._record_callback_event(
            "ibkr_account_callback_quarantined",
            report_id=report_id,
            broker_order_id=broker_order_id,
            execution_id=execution_id,
            reason="wrong_account",
            expected_account=self._mask_account_id(self.connection.account_id),
            observed_account=self._mask_account_id(observed_account),
        )

    @staticmethod
    def _mask_account_id(account_id: str) -> str:
        if len(account_id) <= 4:
            return "*" * len(account_id)
        return f"{account_id[:2]}{'*' * max(len(account_id) - 4, 1)}{account_id[-2:]}"


__all__ = [
    "IbkrExecutionReport",
    "IbkrOrderCallbackEvent",
    "IbkrOrderExecutionAdapter",
    "IbkrOrderExecutionConnection",
    "IbkrOrderContractSpec",
    "IbkrOrderRequest",
]
