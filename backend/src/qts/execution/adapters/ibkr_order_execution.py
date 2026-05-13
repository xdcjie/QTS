"""IBKR order execution adapter skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import BrokerId
from qts.domain.orders import ExecutionReport, OrderIntent
from qts.execution.adapters.ibkr_transport import (
    IbkrCommissionPayload,
    IbkrCommissionReport,
    IbkrConnectionEvent,
    IbkrConnectionEventPayload,
    IbkrErrorPayload,
    IbkrExecutionPayload,
    IbkrOrderContractSpec,
    IbkrOrderRequest,
    IbkrOrderStatusPayload,
    IbkrTransportError,
)
from qts.execution.broker import (
    BrokerCapabilities,
    BrokerExecutionReportStatus,
    BrokerOrderType,
    TimeInForce,
    normalize_broker_status,
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


class IbkrOrderExecutionAdapter:
    """Maps internal orders to IBKR order requests and normalizes reports."""

    def __init__(
        self,
        *,
        connection: IbkrOrderExecutionConnection,
        symbol_mapping: BrokerSymbolMapping,
        capabilities: BrokerCapabilities | None = None,
    ) -> None:
        """Perform __init__."""
        self.connection = connection
        self._symbol_mapping = symbol_mapping
        self._capabilities = capabilities or BrokerCapabilities(
            broker_id=connection.broker_id,
            supports_market_orders=True,
            supports_limit_orders=True,
            supports_cancel=True,
            supports_replace=False,
            supports_fractional=False,
            supports_short=False,
        )
        self._pending_executions: dict[str, IbkrExecutionPayload] = {}
        self._commissions: dict[str, IbkrCommissionPayload] = {}

    def to_order_request(
        self,
        intent: OrderIntent,
        *,
        order_type: BrokerOrderType = BrokerOrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        limit_price: Decimal | None = None,
        asset_class: str = "equity",
        opens_short: bool = False,
        contract: IbkrOrderContractSpec | None = None,
    ) -> IbkrOrderRequest:
        """Perform to_order_request."""
        self._validate_order_request(
            intent,
            order_type=order_type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            asset_class=asset_class,
            opens_short=opens_short,
        )
        return IbkrOrderRequest(
            client_order_id=intent.order_id.value,
            account_id=self.connection.account_id,
            broker_symbol=self._symbol_mapping.to_broker_symbol(intent.instrument_id),
            side=intent.side.value,
            quantity=intent.quantity,
            order_type=order_type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            contract=contract,
        )

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

    def on_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport:
        """Normalize a raw IBKR order-status callback."""

        return self.normalize_execution_report(
            IbkrExecutionReport(
                report_id=payload.report_id,
                broker_order_id=payload.broker_order_id,
                status=self._status_from_ibkr(payload.status),
            )
        )

    def on_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Stage a raw IBKR execution callback until its commission arrives."""

        self._pending_executions[payload.execution_id] = payload
        commission = self._commissions.get(payload.execution_id)
        if commission is None:
            return None
        return self._pop_commissioned_execution(payload.execution_id)

    def on_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Normalize a raw IBKR commission callback and complete matching fills."""

        self._commissions[payload.execution_id] = payload
        report = self._pop_commissioned_execution(payload.execution_id)
        if report is not None:
            return report
        return IbkrCommissionReport(
            execution_id=payload.execution_id,
            commission=payload.commission,
            currency=payload.currency,
        )

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

    def validate_cancel_supported(self) -> None:
        """Validate cancel support before sending an IBKR cancel request."""

        if not self._capabilities.supports_cancel:
            raise ValueError("cancel is not supported by broker capabilities")

    def validate_replace_supported(self) -> None:
        """Validate replace support before sending an IBKR replace request."""

        if not self._capabilities.supports_replace:
            raise ValueError("replace is not supported by broker capabilities")

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
        if order_type is not BrokerOrderType.LIMIT and limit_price is not None:
            raise ValueError("limit_price is only valid for limit orders")
        if (
            not self._capabilities.supports_fractional
            and intent.quantity != intent.quantity.to_integral_value()
        ):
            raise ValueError("fractional quantity is not supported")
        if opens_short and not self._capabilities.supports_short:
            raise ValueError("short orders are not supported")

    def _pop_commissioned_execution(self, execution_id: str) -> ExecutionReport | None:
        execution = self._pending_executions.get(execution_id)
        commission = self._commissions.get(execution_id)
        if execution is None or commission is None:
            return None
        self._pending_executions.pop(execution_id)
        self._commissions.pop(execution_id)
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


__all__ = [
    "IbkrExecutionReport",
    "IbkrOrderExecutionAdapter",
    "IbkrOrderExecutionConnection",
    "IbkrOrderContractSpec",
    "IbkrOrderRequest",
]
