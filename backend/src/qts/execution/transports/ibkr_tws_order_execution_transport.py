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
from qts.domain.orders import BracketLeg, ExecutionReport, ExecutionReportStatus
from qts.execution.broker import BrokerOrderType, TimeInForce
from qts.execution.transports.ibkr_order_ids import IbkrOrderIdAllocator

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
    last_trade_date_or_contract_month: str | None = None

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
        if (
            self.last_trade_date_or_contract_month is not None
            and not self.last_trade_date_or_contract_month.strip()
        ):
            raise ValueError("last_trade_date_or_contract_month must not be empty when provided")

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

    @classmethod
    def future(
        cls,
        broker_symbol: str,
        *,
        exchange: str,
        currency: str,
        last_trade_date_or_contract_month: str,
    ) -> IbkrOrderContractSpec:
        """Create a futures contract spec for an IBKR broker symbol."""

        return cls(
            broker_symbol=broker_symbol,
            security_type="FUT",
            exchange=exchange,
            currency=currency,
            last_trade_date_or_contract_month=last_trade_date_or_contract_month,
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
        if self.last_trade_date_or_contract_month is not None:
            contract.lastTradeDateOrContractMonth = self.last_trade_date_or_contract_month
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
    bracket_legs: tuple[BracketLeg, ...] | None = None
    contract: IbkrOrderContractSpec | None = None
    outside_regular_trading_hours: bool = False
    what_if: bool = False

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
        if self.order_type is BrokerOrderType.BRACKET:
            if self.bracket_legs is None:
                raise ValueError("bracket_legs are required for bracket orders")
            if len(self.bracket_legs) < 2:
                raise ValueError("bracket orders require at least two child legs")
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

        order = self._new_order()
        order.action = self.side.upper()
        order.totalQuantity = self.quantity
        order.tif = self.time_in_force.value.upper()
        order.account = self.account_id
        order.orderRef = self.client_order_id
        order.transmit = True
        order.outsideRth = self.outside_regular_trading_hours
        order.whatIf = self.what_if
        if self.order_type is BrokerOrderType.MARKET:
            order.orderType = "MKT"
        elif self.order_type is BrokerOrderType.LIMIT:
            order.orderType = "LMT"
            order.lmtPrice = float(self.limit_price or Decimal("0"))
        else:
            order.orderType = self.order_type.value.upper()
        return order

    def to_ibapi_bracket_orders(
        self,
        *,
        parent_order_id: int,
        child_order_ids: tuple[int, ...],
    ) -> tuple[Any, ...]:
        """Return parent and OCO child orders for an IBKR bracket request."""

        if self.order_type is not BrokerOrderType.BRACKET:
            raise ValueError("bracket order conversion requires order_type=BRACKET")
        if self.bracket_legs is None:
            raise ValueError("bracket_legs are required for bracket orders")
        if len(child_order_ids) != len(self.bracket_legs):
            raise ValueError("one child order id is required for each bracket leg")

        parent = self._new_order()
        parent.orderId = parent_order_id
        parent.action = self.side.upper()
        parent.totalQuantity = self.quantity
        parent.tif = self.time_in_force.value.upper()
        parent.account = self.account_id
        parent.orderRef = self.client_order_id
        parent.transmit = self.what_if
        parent.outsideRth = self.outside_regular_trading_hours
        parent.whatIf = self.what_if
        if self.limit_price is None:
            parent.orderType = "MKT"
        else:
            parent.orderType = "LMT"
            parent.lmtPrice = float(self.limit_price)

        children: list[Any] = []
        for index, (child_order_id, leg) in enumerate(
            zip(child_order_ids, self.bracket_legs, strict=True)
        ):
            child = self._new_order()
            child.orderId = child_order_id
            child.action = leg.side.upper()
            child.totalQuantity = leg.quantity
            child.tif = self.time_in_force.value.upper()
            child.account = self.account_id
            child.orderRef = f"{self.client_order_id}-bracket-{index + 1}"
            child.parentId = parent_order_id
            child.transmit = self.what_if or index == len(self.bracket_legs) - 1
            child.outsideRth = self.outside_regular_trading_hours
            child.whatIf = self.what_if
            _apply_bracket_leg_price(child, leg)
            children.append(child)

        return (parent, *children)

    @staticmethod
    def _new_order() -> Any:
        order_class = _ibapi_attr("ibapi.order", "Order")
        return order_class()


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
    account_id: str | None = None

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
        if self.account_id is not None and not self.account_id.strip():
            raise ValueError("account_id must not be empty when provided")


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
        from qts.execution.transports.ibkr_tws_callback_dispatcher import (
            IbkrTwsCallbackDispatcher,
        )
        from qts.execution.transports.ibkr_tws_connection import IbkrTwsConnection
        from qts.execution.transports.ibkr_tws_execution_event_emitter import (
            IbkrTwsExecutionEventEmitter,
        )
        from qts.execution.transports.ibkr_tws_order_client import IbkrTwsOrderClient
        from qts.execution.transports.ibkr_tws_reconciliation_client import (
            IbkrTwsReconciliationClient,
        )

        self.config = config
        self._reports: queue.Queue[ExecutionReport | IbkrTransportError | IbkrConnectionEvent] = (
            queue.Queue()
        )
        self._seen_errors: list[IbkrTransportError] = []
        self._connection = IbkrTwsConnection(
            config=config,
            app_factory=_new_order_execution_app,
        )
        self._order_client = IbkrTwsOrderClient(
            config=config,
            sink=sink,
            order_id_allocator=order_id_allocator,
        )
        self._reconciliation_client = IbkrTwsReconciliationClient(config=config)
        self._event_emitter = IbkrTwsExecutionEventEmitter(reports=self._reports)
        self._callback_dispatcher = IbkrTwsCallbackDispatcher(
            sink=sink,
            emitter=self._event_emitter,
        )

    @property
    def _app(self) -> Any | None:
        return self._connection.app

    @_app.setter
    def _app(self, app: Any | None) -> None:
        self._connection.set_app(app)

    @property
    def connected(self) -> bool:
        """Return whether the IBKR client is connected."""

        return self._connection.connected

    @property
    def managed_accounts(self) -> tuple[str, ...]:
        """Return managed accounts advertised by the connected Gateway session."""

        return self._connection.managed_accounts

    def connect(self) -> None:
        """Connect to TWS/Gateway and wait for the next order id."""

        self._connection.connect(self)

    def disconnect(self) -> None:
        """Disconnect from TWS/Gateway."""

        self._connection.disconnect()

    def submit_order(self, request: IbkrOrderRequest) -> None:
        """Submit a normalized IBKR order request."""

        self.submit_order_with_broker_id(request)

    def submit_order_with_broker_id(self, request: IbkrOrderRequest) -> str:
        """Submit an IBKR order request and return the broker order id."""

        return self._order_client.submit_order_with_broker_id(
            self._connection.require_app(),
            request,
        )

    def cancel_order(self, broker_order_id: str) -> None:
        """Cancel a broker order by broker order id."""

        self._order_client.cancel_order(self._connection.require_app(), broker_order_id)

    def request_startup_reconciliation(self) -> None:
        """Request broker state needed to reconcile after startup or reconnect."""

        self._reconciliation_client.request_startup_reconciliation(self._connection.require_app())

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

        return self._callback_dispatcher.handle_order_status(
            order_id=order_id,
            status=status,
            perm_id=perm_id,
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

        self._callback_dispatcher.handle_open_order(
            order_id=order_id,
            order=order,
            order_state=order_state,
            contract=contract,
        )

    def handle_position(self, *, account_id: str, contract: Any, position: object) -> None:
        """Handle an IBKR position callback."""

        self._callback_dispatcher.handle_position(
            account_id=account_id,
            contract=contract,
            position=position,
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

        self._callback_dispatcher.handle_account_summary(
            account_id=account_id,
            tag=tag,
            value=value,
            currency=currency,
        )

    def handle_execution(self, execution: Any) -> ExecutionReport | None:
        """Handle an IBKR execDetails callback."""

        return self._callback_dispatcher.handle_execution(execution)

    def handle_commission_report(self, commission_report: Any) -> None:
        """Handle an IBKR commission callback."""

        self._callback_dispatcher.handle_commission_report(commission_report)

    def handle_commission_and_fees(self, commission_report: Any) -> None:
        """Handle an IBKR commissionAndFeesReport callback."""

        self._callback_dispatcher.handle_commission_and_fees(commission_report)

    def handle_error(self, *, request_id: int, code: int, message: str) -> None:
        """Handle an IBKR error callback."""

        self._callback_dispatcher.handle_error(request_id=request_id, code=code, message=message)

    def handle_disconnect(self, *, reason: str) -> None:
        """Handle an IBKR disconnect callback."""

        self._callback_dispatcher.handle_disconnect(reason=reason)

    def handle_reconnect(self, *, reason: str) -> None:
        """Handle an IBKR reconnect callback."""

        self._callback_dispatcher.handle_reconnect(reason=reason)

    def mark_next_order_id(self, order_id: int) -> None:
        """Record the next valid IBKR order id and mark the API session ready."""

        self._order_client.mark_next_order_id(order_id)
        self._connection.mark_ready()

    def set_managed_accounts(self, accounts: str) -> None:
        """Record managed accounts from the Gateway session."""

        self._connection.set_managed_accounts(accounts)

    def emit_order_status(self, payload: IbkrOrderStatusPayload) -> ExecutionReport | None:
        """Dispatch a raw order-status callback to the adapter sink."""

        return self._callback_dispatcher.dispatch_order_status(payload)

    def emit_open_order(self, payload: IbkrOpenOrderPayload) -> None:
        """Dispatch a raw openOrder callback to the adapter sink."""

        self._callback_dispatcher.dispatch_open_order(payload)

    def emit_execution(self, payload: IbkrExecutionPayload) -> ExecutionReport | None:
        """Dispatch a raw execution callback to the adapter sink."""

        return self._callback_dispatcher.dispatch_execution(payload)

    def emit_commission(
        self,
        payload: IbkrCommissionPayload,
    ) -> ExecutionReport | IbkrCommissionReport:
        """Dispatch a raw commission callback to the adapter sink."""

        return self._callback_dispatcher.dispatch_commission(payload)

    def emit_error(self, payload: IbkrErrorPayload) -> IbkrTransportError:
        """Dispatch a raw error callback to the adapter sink."""

        return self._callback_dispatcher.dispatch_error(payload)

    def emit_disconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw disconnect callback to the adapter sink."""

        return self._callback_dispatcher.dispatch_disconnect(payload)

    def emit_reconnect(self, payload: IbkrConnectionEventPayload) -> IbkrConnectionEvent:
        """Dispatch a raw reconnect callback to the adapter sink."""

        return self._callback_dispatcher.dispatch_reconnect(payload)


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


def _apply_bracket_leg_price(order: Any, leg: BracketLeg) -> None:
    if leg.order_type is BrokerOrderType.LIMIT:
        if leg.limit_price is None:
            raise ValueError("limit bracket legs require limit_price")
        order.orderType = "LMT"
        order.lmtPrice = float(leg.limit_price)
        return
    if leg.order_type is BrokerOrderType.STOP:
        if leg.stop_price is None:
            raise ValueError("stop bracket legs require stop_price")
        order.orderType = "STP"
        order.auxPrice = float(leg.stop_price)
        return
    if leg.order_type is BrokerOrderType.STOP_LIMIT:
        if leg.stop_price is None or leg.limit_price is None:
            raise ValueError("stop_limit bracket legs require stop_price and limit_price")
        order.orderType = "STP LMT"
        order.auxPrice = float(leg.stop_price)
        order.lmtPrice = float(leg.limit_price)
        return
    raise ValueError(f"unsupported bracket leg order type: {leg.order_type.value}")


def _format_error(error: IbkrTransportError) -> str:
    return f"request_id={error.request_id} code={error.code} message={error.message}"
