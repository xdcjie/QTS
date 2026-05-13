from __future__ import annotations

import socket
import time
from contextlib import suppress
from decimal import Decimal
from importlib.util import find_spec
from typing import Protocol

import pytest


class _ManagedAccountTransport(Protocol):
    @property
    def managed_accounts(self) -> tuple[str, ...]:
        """Return managed accounts from the connected broker session."""
        ...


def test_ibkr_gateway_order_lifecycle_anchor_requires_paper_and_real_transport(
    request: pytest.FixtureRequest,
) -> None:
    gateway = request.config.getoption("--ibkr-paper-gateway")
    if gateway is None:
        pytest.skip("--ibkr-paper-gateway is required for the real Gateway anchor")
    if not request.config.getoption("--paper-only"):
        pytest.fail("--paper-only is required for the IBKR order lifecycle anchor")
    if not request.config.getoption("--non-marketable-limit"):
        pytest.fail("--non-marketable-limit is required for the IBKR order lifecycle anchor")

    host, port_text = str(gateway).rsplit(":", maxsplit=1)
    with socket.create_connection((host, int(port_text)), timeout=2):
        pass

    if find_spec("ibapi") is None:
        pytest.skip(
            "official IBKR TWS Python API package is not installed; install the "
            "Python client from the IBKR TWS API download before running real "
            "paper order lifecycle anchors"
        )

    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.domain.orders import ExecutionReportStatus
    from qts.execution.adapters.ibkr_order_execution import (
        IbkrOrderExecutionAdapter,
        IbkrOrderExecutionConnection,
    )
    from qts.execution.adapters.ibkr_transport import (
        IbkrOrderContractSpec,
        IbkrTwsOrderExecutionTransport,
        IbkrTwsOrderExecutionTransportConfig,
    )
    from qts.execution.broker import BrokerOrderType
    from qts.execution.order_manager import OrderIntent, OrderSide
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    callback_adapter = IbkrOrderExecutionAdapter(
        connection=IbkrOrderExecutionConnection(
            host=host,
            port=int(port_text),
            client_id=201,
            broker_id=BrokerId("IBKR"),
            account_id="DU0000000",
        ),
        symbol_mapping=mapping,
    )
    transport = IbkrTwsOrderExecutionTransport(
        config=IbkrTwsOrderExecutionTransportConfig(
            host=host,
            port=int(port_text),
            client_id=201,
            timeout_seconds=25,
        ),
        sink=callback_adapter,
    )
    broker_order_id: str | None = None

    try:
        transport.connect()
        account_id = _select_paper_account(_wait_for_managed_accounts(transport))
        request_adapter = IbkrOrderExecutionAdapter(
            connection=IbkrOrderExecutionConnection(
                host=host,
                port=int(port_text),
                client_id=201,
                broker_id=BrokerId("IBKR"),
                account_id=account_id,
            ),
            symbol_mapping=mapping,
        )
        order_request = request_adapter.to_order_request(
            OrderIntent(
                order_id=OrderId("ibkr-paper-anchor-aapl-buy-1"),
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("1"),
            ),
            order_type=BrokerOrderType.LIMIT,
            limit_price=Decimal("0.01"),
            contract=IbkrOrderContractSpec.stock("AAPL", primary_exchange="ISLAND"),
        )

        broker_order_id = transport.submit_order_with_broker_id(order_request)
        accepted = transport.wait_for_order_status(
            broker_order_id,
            statuses={ExecutionReportStatus.ACCEPTED},
            timeout_seconds=25,
        )
        transport.cancel_order(broker_order_id)
        cancelled = transport.wait_for_order_status(
            broker_order_id,
            statuses={ExecutionReportStatus.CANCELLED},
            timeout_seconds=25,
        )
    finally:
        if broker_order_id is not None and transport.connected:
            with suppress(Exception):
                transport.cancel_order(broker_order_id)
        transport.disconnect()

    assert accepted.broker_order_id == broker_order_id
    assert accepted.status is ExecutionReportStatus.ACCEPTED
    assert cancelled.broker_order_id == broker_order_id
    assert cancelled.status is ExecutionReportStatus.CANCELLED


def _wait_for_managed_accounts(
    transport: _ManagedAccountTransport,
    *,
    timeout_seconds: float = 5,
) -> tuple[str, ...]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        accounts = transport.managed_accounts
        if accounts:
            return accounts
        time.sleep(0.1)
    return transport.managed_accounts


def _select_paper_account(accounts: tuple[str, ...]) -> str:
    paper_accounts = [account for account in accounts if account.upper().startswith("DU")]
    if not paper_accounts:
        pytest.fail("paper-only IBKR order anchor requires a managed DU paper account")
    return paper_accounts[0]
