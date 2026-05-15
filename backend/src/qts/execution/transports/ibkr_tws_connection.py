"""IBKR TWS connection owner for order execution."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrTwsOrderExecutionTransportConfig,
    _connect_ibapi_app,
)


class IbkrTwsConnection:
    """Owns the TWS app socket, reader thread, readiness, and managed accounts."""

    def __init__(
        self,
        *,
        config: IbkrTwsOrderExecutionTransportConfig,
        app_factory: Callable[[Any], Any],
    ) -> None:
        self._config = config
        self._app_factory = app_factory
        self._app: Any | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._managed_accounts: tuple[str, ...] = ()

    @property
    def app(self) -> Any | None:
        """Return the underlying TWS app when initialized."""

        return self._app

    @property
    def connected(self) -> bool:
        """Return whether the underlying TWS app is connected."""

        app = self._app
        return bool(app is not None and app.isConnected())

    @property
    def managed_accounts(self) -> tuple[str, ...]:
        """Return managed accounts advertised by the connected Gateway session."""

        return self._managed_accounts

    def set_app(self, app: Any | None) -> None:
        """Set the underlying app for tests or externally constructed sessions."""

        self._app = app

    def connect(self, owner: Any) -> None:
        """Connect to TWS/Gateway and wait for callback readiness."""

        if self.connected:
            return
        self._ready.clear()
        app = self._app_factory(owner)
        self._app = app
        try:
            _connect_ibapi_app(
                app,
                host=self._config.host,
                port=self._config.port,
                client_id=self._config.client_id,
                timeout_seconds=self._config.timeout_seconds,
            )
            self._thread = threading.Thread(
                target=app.run,
                name=f"qts-ibkr-oe-{self._config.client_id}",
                daemon=True,
            )
            self._thread.start()
            if self._ready.wait(self._config.timeout_seconds):
                return
        except Exception:
            self.disconnect()
            raise
        self.disconnect()
        raise TimeoutError("timed out waiting for IBKR order-execution API readiness")

    def disconnect(self) -> None:
        """Disconnect from TWS/Gateway and stop the reader thread."""

        app = self._app
        if app is not None:
            app.disconnect()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
        self._app = None
        self._thread = None
        self._ready.clear()

    def mark_ready(self) -> None:
        """Mark the connection ready after nextValidId is reconciled."""

        self._ready.set()

    def set_managed_accounts(self, accounts: str) -> None:
        """Record managed accounts from the Gateway session."""

        self._managed_accounts = tuple(
            account.strip() for account in accounts.split(",") if account.strip()
        )

    def require_app(self) -> Any:
        """Return the connected TWS app or raise."""

        app = self._app
        if app is None or not app.isConnected():
            raise RuntimeError("IBKR order-execution transport is not connected")
        return app


__all__ = ["IbkrTwsConnection"]
