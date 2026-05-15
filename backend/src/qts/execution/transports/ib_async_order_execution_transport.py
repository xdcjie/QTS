"""ib_async-backed IBKR order-execution transport."""

from __future__ import annotations

import queue
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from time import monotonic
from typing import Any

from qts.domain.orders import ExecutionReport, ExecutionReportStatus
from qts.execution.broker import BrokerOrderType
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrCommissionPayload,
    IbkrCommissionReport,
    IbkrErrorPayload,
    IbkrExecutionPayload,
    IbkrOrderContractSpec,
    IbkrOrderExecutionCallbackSink,
    IbkrOrderRequest,
    IbkrOrderStatusPayload,
    IbkrTransportError,
)


@dataclass(frozen=True, slots=True)
class IbAsyncOrderExecutionTransportConfig:
    """IB Gateway order-execution settings for an ib_async client."""

    host: str
    port: int
    client_id: int
    timeout_seconds: float = 20.0

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


class IbAsyncOrderExecutionTransport:
    """Submit and monitor IBKR orders through ib_async."""

    def __init__(
        self,
        *,
        config: IbAsyncOrderExecutionTransportConfig,
        sink: IbkrOrderExecutionCallbackSink,
        ib_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.config = config
        self._sink = sink
        self._ib_factory = ib_factory or _default_ib_factory
        self._ib: Any | None = None
        self._reports: queue.Queue[ExecutionReport] = queue.Queue()
        self._errors: queue.Queue[IbkrTransportError] = queue.Queue()
        self._trades_by_broker_order_id: dict[str, Any] = {}
        self._emitted_statuses: set[tuple[str, str]] = set()
        self._emitted_executions: set[str] = set()
        self._managed_accounts: tuple[str, ...] = ()

    @property
    def connected(self) -> bool:
        """Return whether the underlying ib_async client is connected."""

        ib = self._ib
        return bool(ib is not None and ib.isConnected())

    @property
    def managed_accounts(self) -> tuple[str, ...]:
        """Return managed accounts advertised by Gateway."""

        return self._managed_accounts

    def connect(self) -> None:
        """Connect to IB Gateway."""

        if self.connected:
            return
        ib = self._ib_factory()
        ib.connect(
            self.config.host,
            self.config.port,
            clientId=self.config.client_id,
            timeout=self.config.timeout_seconds,
        )
        ib.errorEvent += self._on_error
        self._ib = ib
        self._managed_accounts = tuple(str(account) for account in ib.managedAccounts())

    def disconnect(self) -> None:
        """Disconnect from IB Gateway."""

        ib = self._ib
        if ib is not None:
            ib.disconnect()
        self._ib = None
        self._trades_by_broker_order_id.clear()
        self._managed_accounts = ()
        while not self._reports.empty():
            self._reports.get_nowait()

    def submit_order(self, request: IbkrOrderRequest) -> None:
        """Submit an order without returning its broker id."""

        self.submit_order_with_broker_id(request)

    def submit_order_with_broker_id(self, request: IbkrOrderRequest) -> str:
        """Submit an IBKR order request and return the broker order id."""

        ib = self._require_connected_ib()
        contract = _to_ib_async_contract(request.contract_spec())
        contract = ib.qualifyContracts(contract)[0]
        order = _to_ib_async_order(request)
        trade = ib.placeOrder(contract, order)
        broker_order_id = str(trade.order.orderId)
        self._trades_by_broker_order_id[broker_order_id] = trade
        self._sink.record_submitted_order(request, ibkr_order_id=broker_order_id)
        self._drain_trade_reports(trade)
        return broker_order_id

    def cancel_order(self, broker_order_id: str) -> None:
        """Cancel a broker order by id."""

        trade = self._trades_by_broker_order_id[broker_order_id]
        cancelled = self._require_connected_ib().cancelOrder(trade.order)
        self._drain_trade_reports(cancelled or trade)

    def wait_for_order_status(
        self,
        broker_order_id: str,
        *,
        statuses: set[ExecutionReportStatus],
        timeout_seconds: float | None = None,
    ) -> ExecutionReport:
        """Wait for a matching order status report."""

        if not statuses:
            raise ValueError("statuses must not be empty")
        return self._wait_for_report(
            broker_order_id,
            timeout_seconds=timeout_seconds,
            predicate=lambda report: report.status in statuses,
        )

    def wait_for_fill_report(
        self,
        broker_order_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> ExecutionReport:
        """Wait for a matching fill report."""

        return self._wait_for_report(
            broker_order_id,
            timeout_seconds=timeout_seconds,
            predicate=lambda report: (
                report.fill_id is not None
                and report.filled_quantity > Decimal("0")
                and report.fill_price is not None
            ),
        )

    def _wait_for_report(
        self,
        broker_order_id: str,
        *,
        timeout_seconds: float | None,
        predicate: Callable[[ExecutionReport], bool],
    ) -> ExecutionReport:
        timeout = timeout_seconds or self.config.timeout_seconds
        deadline = monotonic() + timeout
        while True:
            self._drain_trade_reports(self._trades_by_broker_order_id[broker_order_id])
            try:
                report = self._reports.get_nowait()
            except queue.Empty as exc:
                self._raise_error_if_any()
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise TimeoutError("timed out waiting for ib_async order report") from exc
                self._require_connected_ib().sleep(min(0.05, remaining))
                continue
            if report.broker_order_id == broker_order_id and predicate(report):
                return report

    def _raise_error_if_any(self) -> None:
        try:
            error = self._errors.get_nowait()
        except queue.Empty:
            return
        raise RuntimeError(
            "IBKR ib_async order-execution error: "
            f"request_id={error.request_id} code={error.code} message={error.message}"
        )

    def _on_error(
        self,
        request_id: int,
        code: int,
        message: str,
        contract: object | None = None,
    ) -> None:
        del contract
        if message.strip():
            self._errors.put(
                self._sink.on_error(
                    IbkrErrorPayload(request_id=request_id, code=code, message=message)
                )
            )

    def _drain_trade_reports(self, trade: Any) -> None:
        broker_order_id = str(trade.order.orderId)
        status = str(trade.orderStatus.status)
        status_key = (broker_order_id, status)
        if status_key not in self._emitted_statuses:
            self._emitted_statuses.add(status_key)
            status_report = self._sink.on_order_status(
                IbkrOrderStatusPayload(
                    report_id=f"ib-async-status-{broker_order_id}-{status.lower()}",
                    broker_order_id=broker_order_id,
                    status=status,
                )
            )
            if status_report is not None:
                self._reports.put(status_report)
        for fill in tuple(trade.fills):
            execution_id = str(fill.execution.execId)
            if execution_id in self._emitted_executions:
                continue
            execution_report = self._sink.on_execution(
                IbkrExecutionPayload(
                    report_id=f"ib-async-exec-{execution_id}",
                    broker_order_id=str(fill.execution.orderId),
                    execution_id=execution_id,
                    filled_quantity=Decimal(str(fill.execution.shares)),
                    fill_price=Decimal(str(fill.execution.price)),
                )
            )
            commission_result = self._sink.on_commission(
                IbkrCommissionPayload(
                    execution_id=execution_id,
                    commission=Decimal(str(fill.commissionReport.commission)),
                    currency=str(fill.commissionReport.currency),
                )
            )
            self._emitted_executions.add(execution_id)
            if isinstance(execution_report, ExecutionReport):
                self._reports.put(execution_report)
            if isinstance(commission_result, ExecutionReport):
                self._reports.put(commission_result)
            elif isinstance(commission_result, IbkrCommissionReport):
                continue

    def _require_connected_ib(self) -> Any:
        ib = self._ib
        if ib is None or not ib.isConnected():
            raise RuntimeError("ib_async order-execution transport is not connected")
        return ib


def _to_ib_async_contract(contract: IbkrOrderContractSpec) -> Any:
    from ib_async import Contract, Stock

    if contract.security_type.upper() == "STK":
        return Stock(
            contract.broker_symbol,
            contract.exchange,
            contract.currency,
            primaryExchange=contract.primary_exchange or "",
        )
    return Contract(
        symbol=contract.broker_symbol,
        secType=contract.security_type,
        exchange=contract.exchange,
        currency=contract.currency,
        primaryExchange=contract.primary_exchange or "",
    )


def _to_ib_async_order(request: IbkrOrderRequest) -> Any:
    from ib_async import LimitOrder, MarketOrder

    order: Any
    if request.order_type is BrokerOrderType.LIMIT:
        order = LimitOrder(
            request.side.upper(),
            float(request.quantity),
            float(request.limit_price or Decimal("0")),
        )
    else:
        order = MarketOrder(request.side.upper(), float(request.quantity))
    order.account = request.account_id
    order.orderRef = request.client_order_id
    order.tif = request.time_in_force.value.upper()
    order.outsideRth = request.outside_regular_trading_hours
    return order


def _default_ib_factory() -> Any:
    from ib_async import IB

    return IB()


__all__ = ["IbAsyncOrderExecutionTransport", "IbAsyncOrderExecutionTransportConfig"]
