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
    parser.addoption(
        "--operator-confirm-paper-order",
        action="store_true",
        help="Confirm the IBKR paper anchor may submit a tiny paper order.",
    )
    parser.addoption(
        "--live-observation-only",
        action="store_true",
        help="Confirm a live IBKR anchor must remain observation-only.",
    )
    parser.addoption(
        "--config",
        action="store",
        default=None,
        help="Path to environment-gated runtime configuration.",
    )
    parser.addoption(
        "--duration",
        action="store",
        default=None,
        help="Duration selector for soak tests.",
    )
    parser.addoption(
        "--evidence-dir",
        action="store",
        default=None,
        help="Directory containing externally collected readiness evidence.",
    )
