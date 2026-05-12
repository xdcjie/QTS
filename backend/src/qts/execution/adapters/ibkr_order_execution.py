"""IBKR order execution adapter skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import BrokerId
from qts.domain.orders import ExecutionReport, OrderIntent
from qts.execution.broker import BrokerExecutionReportStatus, normalize_broker_status
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
class IbkrOrderRequest:
    """IBKR order request produced at the adapter boundary."""

    client_order_id: str
    account_id: str
    broker_symbol: str
    side: str
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class IbkrExecutionReport:
    """IBKR execution report shape before normalization."""

    report_id: str
    broker_order_id: str
    status: BrokerExecutionReportStatus
    filled_quantity: Decimal = Decimal("0")
    fill_price: Decimal | None = None
    fill_id: str | None = None


class IbkrOrderExecutionAdapter:
    """Maps internal orders to IBKR order requests and normalizes reports."""

    def __init__(
        self,
        *,
        connection: IbkrOrderExecutionConnection,
        symbol_mapping: BrokerSymbolMapping,
    ) -> None:
        """Perform __init__."""
        self.connection = connection
        self._symbol_mapping = symbol_mapping

    def to_order_request(self, intent: OrderIntent) -> IbkrOrderRequest:
        """Perform to_order_request."""
        return IbkrOrderRequest(
            client_order_id=intent.order_id.value,
            account_id=self.connection.account_id,
            broker_symbol=self._symbol_mapping.to_broker_symbol(intent.instrument_id),
            side=intent.side.value,
            quantity=intent.quantity,
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
        )


__all__ = [
    "IbkrExecutionReport",
    "IbkrOrderExecutionAdapter",
    "IbkrOrderExecutionConnection",
    "IbkrOrderRequest",
]
