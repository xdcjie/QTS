from __future__ import annotations

from importlib.util import find_spec
from typing import Protocol

import pytest
from qts.data.adapters.ibkr_transport import (
    IbkrMarketDataCallbackSink,
    IbkrMarketDataContractSpec,
)
from qts.domain.market_data import Bar, Quote, Tick
from qts.domain.orders import ExecutionReport, ExecutionReportStatus
from qts.execution.adapters.ibkr_transport import (
    IbkrOrderExecutionCallbackSink,
    IbkrOrderRequest,
)


class IbkrGatewayMarketDataTransport(Protocol):
    @property
    def connected(self) -> bool:
        """Return whether the transport is connected."""
        ...

    def connect(self) -> None:
        """Connect to Gateway."""
        ...

    def disconnect(self) -> None:
        """Disconnect from Gateway."""
        ...

    def collect_first_event(
        self,
        contract: IbkrMarketDataContractSpec,
        *,
        timeout_seconds: float | None = None,
    ) -> Tick | Quote | Bar:
        """Subscribe and collect one normalized event."""
        ...


class IbkrGatewayOrderExecutionTransport(Protocol):
    @property
    def connected(self) -> bool:
        """Return whether the transport is connected."""
        ...

    @property
    def managed_accounts(self) -> tuple[str, ...]:
        """Return managed accounts from the connected broker session."""
        ...

    def connect(self) -> None:
        """Connect to Gateway."""
        ...

    def disconnect(self) -> None:
        """Disconnect from Gateway."""
        ...

    def submit_order_with_broker_id(self, request: IbkrOrderRequest) -> str:
        """Submit an order and return the broker order id."""
        ...

    def cancel_order(self, broker_order_id: str) -> None:
        """Cancel a broker order."""
        ...

    def wait_for_order_status(
        self,
        broker_order_id: str,
        *,
        statuses: set[ExecutionReportStatus],
        timeout_seconds: float | None = None,
    ) -> ExecutionReport:
        """Wait for a matching order status report."""
        ...

    def wait_for_fill_report(
        self,
        broker_order_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> ExecutionReport:
        """Wait for a fill report."""
        ...


def require_ibkr_transport_sdk(transport_name: str) -> None:
    if transport_name == "official" and find_spec("ibapi") is None:
        pytest.skip("official IBKR TWS Python API package is required")
    if transport_name == "async" and find_spec("ib_async") is None:
        pytest.skip("ib_async package is required")


def market_data_transport(
    *,
    transport_name: str,
    host: str,
    port: int,
    client_id: int,
    sink: IbkrMarketDataCallbackSink,
    timeout_seconds: float = 25,
    market_data_type: int = 3,
) -> IbkrGatewayMarketDataTransport:
    if transport_name == "async":
        from qts.data.adapters.ibkr_async_transport import (
            IbAsyncMarketDataTransport,
            IbAsyncMarketDataTransportConfig,
        )

        return IbAsyncMarketDataTransport(
            config=IbAsyncMarketDataTransportConfig(
                host=host,
                port=port,
                client_id=client_id,
                timeout_seconds=timeout_seconds,
                market_data_type=market_data_type,
            ),
            sink=sink,
        )

    from qts.data.adapters.ibkr_transport import (
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )

    return IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host=host,
            port=port,
            client_id=client_id,
            timeout_seconds=timeout_seconds,
            market_data_type=market_data_type,
        ),
        sink=sink,
    )


def order_execution_transport(
    *,
    transport_name: str,
    host: str,
    port: int,
    client_id: int,
    sink: IbkrOrderExecutionCallbackSink,
    timeout_seconds: float = 25,
) -> IbkrGatewayOrderExecutionTransport:
    if transport_name == "async":
        from qts.execution.adapters.ibkr_async_transport import (
            IbAsyncOrderExecutionTransport,
            IbAsyncOrderExecutionTransportConfig,
        )

        return IbAsyncOrderExecutionTransport(
            config=IbAsyncOrderExecutionTransportConfig(
                host=host,
                port=port,
                client_id=client_id,
                timeout_seconds=timeout_seconds,
            ),
            sink=sink,
        )

    from qts.execution.adapters.ibkr_transport import (
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )

    return IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host=host,
            port=port,
            client_id=client_id,
            timeout_seconds=timeout_seconds,
        ),
        sink=sink,
    )


def wait_for_managed_accounts(
    transport: IbkrGatewayOrderExecutionTransport,
    *,
    timeout_seconds: float = 5,
) -> tuple[str, ...]:
    import time

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        accounts = tuple(str(account) for account in transport.managed_accounts)
        if accounts:
            return accounts
        time.sleep(0.1)
    return tuple(str(account) for account in transport.managed_accounts)
