from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--ibkr-paper-gateway",
        action="store",
        default=None,
        help="IBKR paper Gateway host:port for environment-gated anchors.",
    )
    parser.addoption(
        "--paper-only",
        action="store_true",
        help="Confirm an IBKR Gateway anchor is restricted to paper trading.",
    )
    parser.addoption(
        "--non-marketable-limit",
        action="store_true",
        help="Confirm an IBKR order anchor may use a non-marketable limit order.",
    )
