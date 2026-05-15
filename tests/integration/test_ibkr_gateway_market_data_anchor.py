from __future__ import annotations

import socket

import pytest

from tests.support.ibkr_transports import market_data_transport, require_ibkr_transport_sdk


def test_ibkr_gateway_market_data_subscription_anchor_requires_real_transport(
    request: pytest.FixtureRequest,
) -> None:
    gateway = request.config.getoption("--ibkr-paper-gateway")
    if gateway is None:
        pytest.skip("--ibkr-paper-gateway is required for the real Gateway anchor")

    host, port_text = str(gateway).rsplit(":", maxsplit=1)
    with socket.create_connection((host, int(port_text)), timeout=2):
        pass

    transport_name = request.config.getoption("--ibkr-transport")
    require_ibkr_transport_sdk(transport_name)

    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataContractSpec
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("CASH.IDEALPRO.EUR.USD")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "EUR")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host=host,
            port=int(port_text),
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    transport = market_data_transport(
        transport_name=transport_name,
        host=host,
        port=int(port_text),
        client_id=101,
        sink=adapter,
    )

    try:
        transport.connect()
        event = transport.collect_first_event(
            IbkrMarketDataContractSpec(
                broker_symbol="EUR",
                security_type="CASH",
                exchange="IDEALPRO",
                currency="USD",
            ),
            timeout_seconds=25,
        )
    finally:
        transport.disconnect()

    assert event.instrument_id == instrument_id
