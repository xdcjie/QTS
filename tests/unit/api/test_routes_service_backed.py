"""Prove strategy/order/account routes delegate to their application services.

Each test swaps the route module's service instance for a recording stub and
asserts the route returns the *stub's* value (not a route literal) and that the
service method was actually invoked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient
from qts.api.app import create_app
from qts.api.routes import accounts as accounts_route
from qts.api.routes import orders as orders_route
from qts.api.routes import strategies as strategies_route
from qts.application.dto.control_plane import (
    AccountSnapshotDTO,
    OrderStatusDTO,
    StrategyStatusDTO,
)


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer dev-token"}


@dataclass
class _RecordingStrategyService:
    calls: list[tuple[str, str]] = field(default_factory=list)

    def list_strategies(self) -> tuple[StrategyStatusDTO, ...]:
        self.calls.append(("list", ""))
        return (StrategyStatusDTO(strategy_id="svc-strategy", status="running"),)

    def start(self, strategy_id: str) -> StrategyStatusDTO:
        self.calls.append(("start", strategy_id))
        return StrategyStatusDTO(strategy_id=strategy_id, status="running")

    def stop(self, strategy_id: str) -> StrategyStatusDTO:
        self.calls.append(("stop", strategy_id))
        return StrategyStatusDTO(strategy_id=strategy_id, status="stopped")


@dataclass
class _RecordingOrderService:
    calls: list[str] = field(default_factory=list)

    def order_status(self, order_id: str) -> OrderStatusDTO:
        self.calls.append(order_id)
        return OrderStatusDTO(order_id=order_id, status="filled")


@dataclass
class _RecordingAccountService:
    calls: list[str] = field(default_factory=list)

    def account_snapshot(self, account_id: str) -> AccountSnapshotDTO:
        self.calls.append(account_id)
        return AccountSnapshotDTO(account_id=account_id, cash={"USD": "1234.50"})


def test_strategy_routes_delegate_to_service(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _RecordingStrategyService()
    monkeypatch.setattr(strategies_route, "_strategies", stub)
    client = TestClient(create_app())

    listing = client.get("/strategies", headers=_auth_headers())
    started = client.post("/strategies/svc-strategy/start", headers=_auth_headers())
    stopped = client.post("/strategies/svc-strategy/stop", headers=_auth_headers())

    assert listing.json() == [{"strategy_id": "svc-strategy", "status": "running"}]
    assert started.json() == {"strategy_id": "svc-strategy", "status": "running"}
    assert stopped.json() == {"strategy_id": "svc-strategy", "status": "stopped"}
    assert stub.calls == [
        ("list", ""),
        ("start", "svc-strategy"),
        ("stop", "svc-strategy"),
    ]


def test_order_route_delegates_to_service(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _RecordingOrderService()
    monkeypatch.setattr(orders_route, "_orders", stub)
    client = TestClient(create_app())

    response = client.get("/orders/ord-xyz", headers=_auth_headers())

    assert response.json() == {"order_id": "ord-xyz", "status": "filled"}
    assert stub.calls == ["ord-xyz"]


def test_account_route_delegates_to_service(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _RecordingAccountService()
    monkeypatch.setattr(accounts_route, "_accounts", stub)
    client = TestClient(create_app())

    response = client.get("/accounts/acct-xyz", headers=_auth_headers())

    assert response.json() == {"account_id": "acct-xyz", "cash": {"USD": "1234.50"}}
    assert stub.calls == ["acct-xyz"]
