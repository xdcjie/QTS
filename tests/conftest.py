from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True, scope="session")
def _enable_dev_auth_tokens() -> Iterator[None]:
    """Opt the test session into built-in dev tokens unless already configured.

    Production deployments must never set ``QTS_API_DEV_TOKENS``. Tests opt in
    here so the default-deny `StaticTokenAuthBackend` does not break compatibility
    fixtures that issue ``Authorization: Bearer dev-token``.
    """
    if (
        os.getenv("QTS_API_JWT_SECRET") is None
        and os.getenv("QTS_API_STATIC_TOKENS") is None
        and os.getenv("QTS_API_DEV_TOKENS") is None
    ):
        os.environ["QTS_API_DEV_TOKENS"] = "1"
    yield


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--ibkr-paper-gateway",
        action="store",
        default=None,
        help="IBKR paper Gateway host:port for environment-gated anchors.",
    )
    parser.addoption(
        "--ibkr-transport",
        action="store",
        default="official",
        choices=("official", "async"),
        help="IBKR transport implementation for environment-gated anchors.",
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
