from __future__ import annotations

import socket

import pytest


def test_ibkr_paper_session_soak_requires_full_session_gate(
    request: pytest.FixtureRequest,
) -> None:
    gateway = request.config.getoption("--ibkr-paper-gateway")
    if gateway is None:
        pytest.skip("--ibkr-paper-gateway is required for the paper soak")
    if not request.config.getoption("--paper-only"):
        pytest.fail("--paper-only is required for the paper soak")
    if request.config.getoption("--duration") != "full-session":
        pytest.fail("--duration full-session is required for readiness soak evidence")

    host, port_text = str(gateway).rsplit(":", maxsplit=1)
    with socket.create_connection((host, int(port_text)), timeout=2):
        pass

    pytest.skip(
        "full-session paper soak must be run by an operator and archived as "
        "paper-soak evidence before live readiness can be claimed"
    )
