"""IBKR order-execution transport boundary contracts."""

from __future__ import annotations

import queue
import threading
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from time import monotonic
from typing import Any, Literal, Protocol

from qts.core.ids import AccountId, OrderId, StrategyId
from qts.domain.orders import ExecutionReport, ExecutionReportStatus
from qts.execution.adapters.ibkr_order_ids import IbkrOrderIdAllocator
from qts.execution.broker import BrokerOrderType, TimeInForce

_IBKR_INFO_ERROR_CODES = frozenset(
    {399, 1100, 1101, 1102, 1104, 2103, 2104, 2105, 2106, 2107, 2108, 2110, 2119, 2157, 2158}
)
_ORDER_STATUS_REPORT_PREFIX = "ibkr-status"
_EXECUTION_REPORT_PREFIX = "ibkr-exec"


@dataclass(frozen=True, slots=True)
class IbkrOrderContractSpec:
    """IBKR contract fields required for order requests."""

    broker_symbol: str
    security_type: str
    exchange: str
    currency: str
    primary_exchange: str | None = None

    def __post_init__(self) -> None:
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")
        if not self.security_type.strip():
            raise ValueError("security_type must not be empty")
        if not self.exchange.strip():
            raise ValueError("exchange must not be empty")
        if not self.currency.strip():
            raise ValueError("currency must not be empty")
        if self.primary_exchange is not None and not self.primary_exchange.strip():
            raise ValueError("primary_exchange must not be empty when provided")

    @classmethod
    def stock(
        cls,
        broker_symbol: str,
        *,
        exchange: str = "SMART",
        currency: str = "USD",
        primary_exchange: str | None = None,
    ) -> IbkrOrderContractSpec:
        """Create a stock contract spec for an IBKR broker symbol."""

        return cls(
            broker_symbol=broker_symbol,
            security_type="STK",
            exchange=exchange,
            currency=currency,
            primary_exchange=primary_exchange,
        )

    def to_ibapi_contract(self) -> Any:
        """Return an official ibapi Contract object for this spec."""

        contract_class = _ibapi_attr("ibapi.contract", "Contract")
        contract = contract_class()
        contract.symbol = self.broker_symbol
        contract.secType = self.security_type
        contract.exchange = self.exchange
        contract.currency = self.currency
        if self.primary_exchange is not None:
            contract.primaryExchange = self.primary_exchange
        return contract


@dataclass(frozen=True, slots=True)
class IbkrTwsOrderExecutionTransportConfig:
    """IBKR TWS/Gateway order-execution transport settings."""

    host: str
    port: int
    client_id: int
    timeout_seconds: float = 20.0
    order_id_store_path: str | Path | None = None
    request_all_open_orders_on_reconnect: bool = False

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True, slots=True)
class IbkrOrderRequest:
    """IBKR order request produced at the adapter boundary."""

    internal_order_id: OrderId
    client_order_id: str
    internal_account_id: AccountId | None
    strategy_id: StrategyId | None
    account_id: str
    broker_symbol: str
    side: str
    quantity: Decimal
    order_type: BrokerOrderType = BrokerOrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.DAY
    limit_price: Decimal | None = None
    contract: IbkrOrderContractSpec | None = None
    outside_regular_trading_hours: bool = False

    def __post_init__(self) -> None:
        if not self.client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")
        if not self.side.strip():
            raise ValueError("side must not be empty")
        if self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive")
        if self.order_type is BrokerOrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if self.limit_price is not None and self.limit_price <= Decimal("0"):
            raise ValueError("limit_price must be positive")
        if self.contract is not None and self.contract.broker_symbol != self.broker_symbol:
            raise ValueError("contract broker_symbol must match request broker_symbol")

    def contract_spec(self) -> IbkrOrderContractSpec:
        """Return the IBKR contract spec for this order request."""

        return self.contract or IbkrOrderContractSpec.stock(self.broker_symbol)

    def to_ibapi_contract(self) -> Any:
        """Return an official ibapi Contract object for this order request."""

        return self.contract_spec().to_ibapi_contract()

    def to_ibapi_order(self) -> Any:
        """Return an official ibapi Order object for this request."""

        order_class = _ibapi_attr("ibapi.order", "Order")
        order = order_class()
        order.action = self.side.upper()
        order.totalQuantity = self.quantity
        order.tif = self.time_in_force.value.upper()
        order.account = self.account_id
        order.orderRef = self.client_order_id
        order.transmit = True
        order.outsideRth = self.outside_regular_trading_hours
        if self.order_type is BrokerOrderType.MARKET:
            order.orderType = "MKT"
        elif self.order_type is BrokerOrderType.LIMIT:
            order.orderType = "LMT"
            order.lmtPrice = float(self.limit_price or Decimal("0"))
        else:
            order.orderType = self.order_type.value.upper()
        return order


@dataclass(frozen=True, slots=True)
class IbkrOrderStatusPayload:
    """Raw IBKR order-status callback payload."""

    report_id: str
    broker_order_id: str
    status: str
    perm_id: str | None = None

    def __post_init__(self) -> None:
        if not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if not self.status.strip():
            raise ValueError("status must not be empty")
        if self.perm_id is not None and not self.perm_id.strip():
            raise ValueError("perm_id must not be empty when provided")


@dataclass(frozen=True, slots=True)
class IbkrOpenOrderPayload:
    """Raw IBKR openOrder callback payload."""

    report_id: str
    broker_order_id: str
    client_order_id: str | None
    perm_id: str | None = None
    status: str | None = None
    broker_symbol: str | None = None
    side: str | None = None
    quantity: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if self.client_order_id is not None and not self.client_order_id.strip():
            raise ValueError("client_order_id must not be empty when provided")
        if self.perm_id is not None and not self.perm_id.strip():
            raise ValueError("perm_id must not be empty when provided")
        if self.status is not None and not self.status.strip():
            raise ValueError("status must not be empty when provided")
        if self.broker_symbol is not None and not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty when provided")
        if self.side is not None and not self.side.strip():
            raise ValueError("side must not be empty when provided")
        if self.quantity is not None and self.quantity <= Decimal("0"):
            raise ValueError("quantity must be positive when provided")


@dataclass(frozen=True, slots=True)
class IbkrPositionPayload:
    """Raw IBKR position callback payload for reconciliation."""

    account_id: str
    broker_symbol: str
    quantity: Decimal

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrAccountSummaryPayload:
    """Raw IBKR accountSummary callback payload for reconciliation."""

    account_id: str
    tag: str
    value: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if not self.tag.strip():
            raise ValueError("tag must not be empty")
        if not self.currency.strip():
            raise ValueError("currency must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrExecutionPayload:
    """Raw IBKR execution callback payload."""

    report_id: str
    broker_order_id: str
    execution_id: str
    filled_quantity: Decimal
    fill_price: Decimal

    def __post_init__(self) -> None:
        if not self.report_id.strip():
            raise ValueError("report_id must not be empty")
        if not self.broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if not self.execution_id.strip():
            raise ValueError("execution_id must not be empty")
        if self.filled_quantity <= Decimal("0"):
            raise ValueError("filled_quantity must be positive")
        if self.fill_price < Decimal("0"):
            raise ValueError("fill_price must be non-negative")


@dataclass(frozen=True, slots=True)
class IbkrCommissionPayload:
    """Raw IBKR commission callback payload."""

    execution_id: str
    commission: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not self.execution_id.strip():
            raise ValueError("execution_id must not be empty")
        if self.commission < Decimal("0"):
            raise ValueError("commission must be non-negative")
        if not self.currency.strip():
            raise ValueError("currency must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrErrorPayload:
    """Raw IBKR error callback payload."""

    request_id: int
    code: int
    message: str

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrConnectionEventPayload:
    """Raw IBKR disconnect/reconnect payload."""

    reason: str

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrCommissionReport:
    """Normalized commission callback at the adapter boundary."""

    execution_id: str
    commission: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class IbkrTransportError:
    """Normalized IBKR transport error at the adapter boundary."""

    request_id: int
    code: int
    message: str


@dataclass(frozen=True, slots=True)
class IbkrConnectionEvent:
    """Normalized IBKR transport connection event."""

    kind: Literal["disconnect", "reconnect"]
    reason: str


class IbkrOrderExecutionCallbackSink(Protocol):
    """IBKR order-execution callback sink owned by the execution adapter."""

    def record_submitted_order(
        self,
        request: IbkrOrderRequest,
        *,
        ibkr_order_id: str,
        submitted_at: datetime | None = None,
    ) -> None:
        """Record the broker order id assigned during submission."""
        ...

    def on_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Normalize a raw order-status callback."""
        ...

    def on_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Record a raw openOrder callback."""
        ...

    def on_position(self, payload: IbkrPositionPayload) -> None:
        """Record a raw position callback."""
        ...

    def on_account_summary(self, payload: IbkrAccountSummaryPayload) -> None:
        """Record a raw account summary callback."""
        ...

    def on_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Stage or normalize a raw execution callback."""
        ...

    def on_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Normalize a raw commission callback, completing a pending fill when possible."""
        ...

    def on_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        """Normalize a raw error callback."""
        ...

    def on_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Normalize a raw disconnect callback."""
        ...

    def on_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Normalize a raw reconnect callback."""
        ...


class IbkrOrderExecutionTransport(Protocol):
    """Transport interface for IBKR order-execution connectivity."""

    @property
    def connected(self) -> bool:
        """Return whether the transport is connected."""
        ...

    def connect(self) -> None:
        """Connect the order-execution transport."""
        ...

    def disconnect(self) -> None:
        """Disconnect the order-execution transport."""
        ...

    def submit_order(self, request: IbkrOrderRequest) -> None:
        """Submit a normalized IBKR order request."""
        ...

    def cancel_order(self, broker_order_id: str) -> None:
        """Cancel a broker order by broker order id."""
        ...

    def emit_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Dispatch a raw order-status callback to the adapter sink."""
        ...

    def emit_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Dispatch a raw execution callback to the adapter sink."""
        ...

    def emit_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Dispatch a raw commission callback to the adapter sink."""
        ...

    def emit_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        """Dispatch a raw error callback to the adapter sink."""
        ...

    def emit_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw disconnect callback to the adapter sink."""
        ...

    def emit_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw reconnect callback to the adapter sink."""
        ...


class IbkrTwsOrderExecutionTransport:
    """Official IBKR TWS API transport for paper/live order execution."""

    def __init__(
        self,
        *,
        config: IbkrTwsOrderExecutionTransportConfig,
        sink: IbkrOrderExecutionCallbackSink,
        order_id_allocator: IbkrOrderIdAllocator | None = None,
    ) -> None:
        self.config = config
        self._sink = sink
        self._app: Any | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._order_id_allocator = order_id_allocator or IbkrOrderIdAllocator(
            config.order_id_store_path
        )
        self._reports: queue.Queue[ExecutionReport | IbkrTransportError | IbkrConnectionEvent] = (
            queue.Queue()
        )
        self._seen_errors: list[IbkrTransportError] = []
        self._managed_accounts: tuple[str, ...] = ()
        self._submitted_requests: dict[str, IbkrOrderRequest] = {}
        self._request_sequence = 0

    @property
    def connected(self) -> bool:
        """Return whether the IBKR client is connected."""

        app = self._app
        return bool(app is not None and app.isConnected())

    @property
    def managed_accounts(self) -> tuple[str, ...]:
        """Return managed accounts advertised by the connected Gateway session."""

        return self._managed_accounts

    def connect(self) -> None:
        """Connect to TWS/Gateway and wait for the next order id."""

        if self.connected:
            return
        self._ready.clear()
        app = _new_order_execution_app(self)
        self._app = app
        try:
            _connect_ibapi_app(
                app,
                host=self.config.host,
                port=self.config.port,
                client_id=self.config.client_id,
                timeout_seconds=self.config.timeout_seconds,
            )
            self._thread = threading.Thread(
                target=app.run,
                name=f"qts-ibkr-oe-{self.config.client_id}",
                daemon=True,
            )
            self._thread.start()
            if self._ready.wait(self.config.timeout_seconds):
                return
        except Exception:
            self.disconnect()
            raise
        self.disconnect()
        raise TimeoutError("timed out waiting for IBKR order-execution API readiness")

    def disconnect(self) -> None:
        """Disconnect from TWS/Gateway."""

        app = self._app
        if app is not None:
            app.disconnect()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
        self._app = None
        self._thread = None
        self._ready.clear()

    def submit_order(self, request: IbkrOrderRequest) -> None:
        """Submit a normalized IBKR order request."""

        self.submit_order_with_broker_id(request)

    def submit_order_with_broker_id(self, request: IbkrOrderRequest) -> str:
        """Submit an IBKR order request and return the broker order id."""

        app = self._require_connected_app()
        broker_order_id = str(self._reserve_order_id())
        self._submitted_requests[broker_order_id] = request
        app.placeOrder(
            int(broker_order_id),
            request.to_ibapi_contract(),
            request.to_ibapi_order(),
        )
        self._sink.record_submitted_order(request, ibkr_order_id=broker_order_id)
        return broker_order_id

    def cancel_order(self, broker_order_id: str) -> None:
        """Cancel a broker order by broker order id."""

        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        app = self._require_connected_app()
        order_cancel_class = _ibapi_attr("ibapi.order_cancel", "OrderCancel")
        app.cancelOrder(int(broker_order_id), order_cancel_class())

    def request_startup_reconciliation(self) -> None:
        """Request broker state needed to reconcile after startup or reconnect."""

        app = self._require_connected_app()
        app.reqOpenOrders()
        if self.config.request_all_open_orders_on_reconnect:
            app.reqAllOpenOrders()
        app.reqPositions()
        execution_filter_class = _ibapi_attr("ibapi.execution", "ExecutionFilter")
        app.reqExecutions(self._reserve_request_id(), execution_filter_class())
        app.reqAccountSummary(
            self._reserve_request_id(),
            "All",
            "NetLiquidation,TotalCashValue,AvailableFunds",
        )

    def wait_for_order_status(
        self,
        broker_order_id: str,
        *,
        statuses: set[ExecutionReportStatus],
        timeout_seconds: float | None = None,
    ) -> ExecutionReport:
        """Wait for a broker status report matching the order and allowed statuses."""

        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")
        if not statuses:
            raise ValueError("statuses must not be empty")

        timeout = timeout_seconds or self.config.timeout_seconds
        deadline = monotonic() + timeout
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                details = "; ".join(_format_error(error) for error in self._seen_errors)
                suffix = f" IBKR errors: {details}" if details else ""
                raise TimeoutError(f"timed out waiting for IBKR order status.{suffix}")
            try:
                event = self._reports.get(timeout=min(0.25, remaining))
            except queue.Empty:
                continue
            if isinstance(event, IbkrTransportError):
                self._seen_errors.append(event)
                if event.code not in _IBKR_INFO_ERROR_CODES:
                    raise RuntimeError(f"IBKR order-execution error: {_format_error(event)}")
                continue
            if isinstance(event, IbkrConnectionEvent):
                continue
            if event.broker_order_id == broker_order_id and event.status in statuses:
                return event

    def wait_for_fill_report(
        self,
        broker_order_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> ExecutionReport:
        """Wait for a broker fill report with quantity, price, and fill id."""

        if not broker_order_id.strip():
            raise ValueError("broker_order_id must not be empty")

        timeout = timeout_seconds or self.config.timeout_seconds
        deadline = monotonic() + timeout
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                details = "; ".join(_format_error(error) for error in self._seen_errors)
                suffix = f" IBKR errors: {details}" if details else ""
                raise TimeoutError(f"timed out waiting for IBKR fill report.{suffix}")
            try:
                event = self._reports.get(timeout=min(0.25, remaining))
            except queue.Empty:
                continue
            if isinstance(event, IbkrTransportError):
                self._seen_errors.append(event)
                if event.code not in _IBKR_INFO_ERROR_CODES:
                    raise RuntimeError(f"IBKR order-execution error: {_format_error(event)}")
                continue
            if isinstance(event, IbkrConnectionEvent):
                continue
            if (
                event.broker_order_id == broker_order_id
                and event.fill_id is not None
                and event.filled_quantity > Decimal("0")
                and event.fill_price is not None
            ):
                return event

    def handle_order_status(
        self,
        *,
        order_id: int,
        status: str,
        perm_id: int | None = None,
    ) -> ExecutionReport | None:
        """Handle an IBKR orderStatus callback."""

        return self.emit_order_status(
            IbkrOrderStatusPayload(
                report_id=f"{_ORDER_STATUS_REPORT_PREFIX}-{order_id}-{status.lower()}",
                broker_order_id=str(order_id),
                status=status,
                perm_id=None if perm_id is None else str(perm_id),
            )
        )

    def handle_open_order(
        self,
        *,
        order_id: int,
        order: Any,
        order_state: Any,
        contract: Any | None = None,
    ) -> None:
        """Handle an IBKR openOrder callback."""

        order_ref = str(getattr(order, "orderRef", "")).strip()
        perm_id = getattr(order, "permId", None)
        status = str(getattr(order_state, "status", "")).strip()
        total_quantity = order.totalQuantity if hasattr(order, "totalQuantity") else None
        self.emit_open_order(
            IbkrOpenOrderPayload(
                report_id=f"ibkr-open-order-{order_id}",
                broker_order_id=str(order_id),
                client_order_id=order_ref or None,
                perm_id=None if perm_id in {None, 0, ""} else str(perm_id),
                status=status or None,
                broker_symbol=(
                    str(getattr(contract, "symbol", "")).strip() if contract is not None else None
                )
                or None,
                side=str(getattr(order, "action", "")).strip() or None,
                quantity=None if total_quantity in {None, ""} else _to_decimal(total_quantity),
            )
        )

    def handle_position(self, *, account_id: str, contract: Any, position: object) -> None:
        """Handle an IBKR position callback."""

        self._sink.on_position(
            IbkrPositionPayload(
                account_id=account_id,
                broker_symbol=str(getattr(contract, "symbol", "")).strip(),
                quantity=_to_decimal(position),
            )
        )

    def handle_account_summary(
        self,
        *,
        account_id: str,
        tag: str,
        value: object,
        currency: str,
    ) -> None:
        """Handle an IBKR accountSummary callback."""

        self._sink.on_account_summary(
            IbkrAccountSummaryPayload(
                account_id=account_id,
                tag=tag,
                value=_to_decimal(value),
                currency=currency,
            )
        )

    def handle_execution(self, execution: Any) -> ExecutionReport | None:
        """Handle an IBKR execDetails callback."""

        return self.emit_execution(
            IbkrExecutionPayload(
                report_id=f"{_EXECUTION_REPORT_PREFIX}-{execution.execId}",
                broker_order_id=str(execution.orderId),
                execution_id=str(execution.execId),
                filled_quantity=_to_decimal(execution.shares),
                fill_price=_to_decimal(execution.price),
            )
        )

    def handle_commission_report(self, commission_report: Any) -> None:
        """Handle an IBKR commission callback."""

        commission = (
            commission_report.commissionAndFees
            if hasattr(commission_report, "commissionAndFees")
            else commission_report.commission
        )
        result = self.emit_commission(
            IbkrCommissionPayload(
                execution_id=str(commission_report.execId),
                commission=_to_decimal(commission),
                currency=str(commission_report.currency),
            )
        )
        if isinstance(result, ExecutionReport):
            self._reports.put(result)

    def handle_commission_and_fees(self, commission_report: Any) -> None:
        """Handle an IBKR commissionAndFeesReport callback."""

        self.handle_commission_report(commission_report)

    def handle_error(self, *, request_id: int, code: int, message: str) -> None:
        """Handle an IBKR error callback."""

        if message.strip():
            self._reports.put(
                self.emit_error(IbkrErrorPayload(request_id=request_id, code=code, message=message))
            )

    def handle_disconnect(self, *, reason: str) -> None:
        """Handle an IBKR disconnect callback."""

        self._reports.put(self.emit_disconnect(IbkrConnectionEventPayload(reason=reason)))

    def handle_reconnect(self, *, reason: str) -> None:
        """Handle an IBKR reconnect callback."""

        self._reports.put(self.emit_reconnect(IbkrConnectionEventPayload(reason=reason)))

    def mark_next_order_id(self, order_id: int) -> None:
        """Record the next valid IBKR order id and mark the API session ready."""

        if order_id <= 0:
            raise ValueError("order_id must be positive")
        self._order_id_allocator.reconcile_next_valid_id(
            client_id=self.config.client_id,
            broker_next_valid_id=order_id,
        )
        self._ready.set()

    def set_managed_accounts(self, accounts: str) -> None:
        """Record managed accounts from the Gateway session."""

        self._managed_accounts = tuple(
            account.strip() for account in accounts.split(",") if account.strip()
        )

    def emit_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Dispatch a raw order-status callback to the adapter sink."""

        report = self._sink.on_order_status(payload)
        if report is not None:
            self._reports.put(report)
        return report

    def emit_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Dispatch a raw openOrder callback to the adapter sink."""

        self._sink.on_open_order(payload)

    def emit_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Dispatch a raw execution callback to the adapter sink."""

        report = self._sink.on_execution(payload)
        if report is not None:
            self._reports.put(report)
        return report

    def emit_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Dispatch a raw commission callback to the adapter sink."""

        return self._sink.on_commission(payload)

    def emit_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        """Dispatch a raw error callback to the adapter sink."""

        return self._sink.on_error(payload)

    def emit_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw disconnect callback to the adapter sink."""

        return self._sink.on_disconnect(payload)

    def emit_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw reconnect callback to the adapter sink."""

        return self._sink.on_reconnect(payload)

    def _reserve_order_id(self) -> int:
        if self._order_id_allocator.next_id(client_id=self.config.client_id) is None:
            raise RuntimeError("IBKR order-execution transport has no next order id")
        return self._order_id_allocator.allocate(client_id=self.config.client_id)

    def _reserve_request_id(self) -> int:
        self._request_sequence += 1
        return self._request_sequence

    def _require_connected_app(self) -> Any:
        app = self._app
        if app is None or not app.isConnected():
            raise RuntimeError("IBKR order-execution transport is not connected")
        return app


__all__ = [
    "IbkrCommissionPayload",
    "IbkrCommissionReport",
    "IbkrConnectionEvent",
    "IbkrConnectionEventPayload",
    "IbkrErrorPayload",
    "IbkrExecutionPayload",
    "IbkrAccountSummaryPayload",
    "IbkrOpenOrderPayload",
    "IbkrOrderContractSpec",
    "IbkrOrderExecutionCallbackSink",
    "IbkrOrderExecutionTransport",
    "IbkrOrderRequest",
    "IbkrOrderStatusPayload",
    "IbkrPositionPayload",
    "IbkrTransportError",
    "IbkrTwsOrderExecutionTransport",
    "IbkrTwsOrderExecutionTransportConfig",
]


def _new_order_execution_app(owner: IbkrTwsOrderExecutionTransport) -> Any:
    wrapper_class = _ibapi_attr("ibapi.wrapper", "EWrapper")
    client_class = _ibapi_attr("ibapi.client", "EClient")

    def __init__(self: Any) -> None:
        wrapper_class.__init__(self)
        client_class.__init__(self, self)

    def next_valid_id(self: Any, order_id: int) -> None:
        owner.mark_next_order_id(order_id)

    def managed_accounts(self: Any, accounts_list: str) -> None:
        owner.set_managed_accounts(accounts_list)

    def order_status(
        self: Any,
        order_id: int,
        status: str,
        filled: Decimal,
        remaining: Decimal,
        avg_fill_price: float,
        perm_id: int,
        parent_id: int,
        last_fill_price: float,
        client_id: int,
        why_held: str,
        mkt_cap_price: float,
    ) -> None:
        del (
            filled,
            remaining,
            avg_fill_price,
            parent_id,
            last_fill_price,
            client_id,
            why_held,
            mkt_cap_price,
        )
        owner.handle_order_status(order_id=order_id, status=status, perm_id=perm_id)

    def open_order(self: Any, order_id: int, contract: Any, order: Any, order_state: Any) -> None:
        owner.handle_open_order(
            order_id=order_id,
            contract=contract,
            order=order,
            order_state=order_state,
        )

    def position(self: Any, account: str, contract: Any, pos: Decimal, avg_cost: float) -> None:
        del avg_cost
        owner.handle_position(account_id=account, contract=contract, position=pos)

    def account_summary(
        self: Any,
        req_id: int,
        account: str,
        tag: str,
        value: str,
        currency: str,
    ) -> None:
        del req_id
        owner.handle_account_summary(
            account_id=account,
            tag=tag,
            value=value,
            currency=currency,
        )

    def exec_details(self: Any, req_id: int, contract: Any, execution: Any) -> None:
        del req_id, contract
        owner.handle_execution(execution)

    def commission_and_fees_report(self: Any, commission_report: Any) -> None:
        owner.handle_commission_and_fees(commission_report)

    def commission_report(self: Any, commission_report: Any) -> None:
        owner.handle_commission_report(commission_report)

    def error(
        self: Any,
        req_id: int,
        error_time: int,
        error_code: int,
        error_string: str,
        advanced_order_reject_json: str = "",
    ) -> None:
        del error_time, advanced_order_reject_json
        owner.handle_error(request_id=req_id, code=error_code, message=error_string)

    def connection_closed(self: Any) -> None:
        owner.handle_disconnect(reason="socket closed")

    app_class = type(
        "_QtsIbkrOrderExecutionApp",
        (wrapper_class, client_class),
        {
            "__init__": __init__,
            "nextValidId": next_valid_id,
            "managedAccounts": managed_accounts,
            "orderStatus": order_status,
            "openOrder": open_order,
            "position": position,
            "accountSummary": account_summary,
            "execDetails": exec_details,
            "commissionAndFeesReport": commission_and_fees_report,
            "commissionReport": commission_report,
            "error": error,
            "connectionClosed": connection_closed,
        },
    )
    return app_class()


def _ibapi_attr(module_name: str, attribute_name: str) -> Any:
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "official IBKR TWS Python API package is required; install ibapi from "
            "the Interactive Brokers TWS API download"
        ) from exc
    return getattr(module, attribute_name)


def _connect_ibapi_app(
    app: Any,
    *,
    host: str,
    port: int,
    client_id: int,
    timeout_seconds: float,
) -> None:
    errors: list[BaseException] = []

    def connect() -> None:
        try:
            app.connect(host, port, client_id)
        except BaseException as exc:  # pragma: no cover - re-raised on caller thread
            errors.append(exc)

    thread = threading.Thread(
        target=connect,
        name=f"qts-ibkr-connect-{client_id}",
        daemon=True,
    )
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        with suppress(Exception):
            app.disconnect()
        thread.join(timeout=1)
        raise TimeoutError("timed out connecting to IBKR API")
    if errors:
        raise errors[0]


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _format_error(error: IbkrTransportError) -> str:
    return f"request_id={error.request_id} code={error.code} message={error.message}"
