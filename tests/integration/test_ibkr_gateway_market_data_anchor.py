from __future__ import annotations

import socket
from importlib.util import find_spec

import pytest


def test_ibkr_gateway_market_data_subscription_anchor_requires_real_transport(
    request: pytest.FixtureRequest,
) -> None:
    gateway = request.config.getoption("--ibkr-paper-gateway")
    if gateway is None:
        pytest.skip("--ibkr-paper-gateway is required for the real Gateway anchor")

    host, port_text = str(gateway).rsplit(":", maxsplit=1)
    with socket.create_connection((host, int(port_text)), timeout=2):
        pass

    if find_spec("ibapi") is None:
        pytest.skip(
            "official IBKR TWS Python API package is not installed; install the "
            "Python client from the IBKR TWS API download before running real "
            "market-data subscription anchors"
        )

    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.adapters.ibkr_transport import (
        IbkrMarketDataContractSpec,
        IbkrTwsMarketDataTransport,
        IbkrTwsMarketDataTransportConfig,
    )
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
    transport = IbkrTwsMarketDataTransport(
        config=IbkrTwsMarketDataTransportConfig(
            host=host,
            port=int(port_text),
            client_id=101,
            timeout_seconds=25,
            market_data_type=3,
        ),
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
