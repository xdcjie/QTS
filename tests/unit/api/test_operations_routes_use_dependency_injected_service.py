"""Operations routes resolve OperationsService via DI, not a module global.

QTS-FINAL-001: operator control-plane routes must resolve their OperationsService
through FastAPI dependency injection / app state so the service can be bound to a
real runtime at app construction. These tests lock that the route uses the
app-state-injected instance and that the module-global anti-pattern is gone.
"""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient
from qts.api.app import create_app
from qts.application.dto import OperatorDashboardStatusDTO
from qts.application.services import OperationsService

_OPERATIONS_ROUTE_SOURCE = Path("backend/src/qts/api/routes/operations.py").read_text(
    encoding="utf-8"
)


def _auth_headers(**extra: str) -> dict[str, str]:
    headers = {"Authorization": "Bearer dev-token"}
    headers.update(extra)
    return headers


class _RecordingOperationsService(OperationsService):
    """OperationsService that records that the route resolved this instance."""

    def __init__(self) -> None:
        super().__init__()
        self.operator_status_calls = 0

    def operator_status(self) -> OperatorDashboardStatusDTO:
        self.operator_status_calls += 1
        return super().operator_status()


def test_route_uses_app_state_injected_operations_service() -> None:
    injected = _RecordingOperationsService()
    client = TestClient(create_app(operations_service=injected))

    response = client.get(
        "/operations/operator-status",
        headers=_auth_headers(**{"X-QTS-Operator": "tester"}),
    )

    assert response.status_code == 200
    assert injected.operator_status_calls == 1


def test_independent_apps_use_independent_injected_services() -> None:
    service_a = _RecordingOperationsService()
    service_b = _RecordingOperationsService()
    client_a = TestClient(create_app(operations_service=service_a))
    # A second app bound to service_b; requests to client_a must not touch it.
    TestClient(create_app(operations_service=service_b))

    client_a.get(
        "/operations/operator-status",
        headers=_auth_headers(**{"X-QTS-Operator": "tester"}),
    )

    assert service_a.operator_status_calls == 1
    assert service_b.operator_status_calls == 0


def test_operations_route_module_has_no_module_global_service() -> None:
    tree = ast.parse(_OPERATIONS_ROUTE_SOURCE)
    module_assignments = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    # The module-global OperationsService()/CommandIdempotencyStore() singletons are gone.
    assert "_operations" not in module_assignments
    assert "_idempotency" not in module_assignments
    # The DI providers exist instead.
    function_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "get_operations_service" in function_names
    assert "get_command_idempotency" in function_names
