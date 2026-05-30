"""Boundary gate: ExecutionReportHandler does not reach into account state (DR-021)."""

from __future__ import annotations

import inspect

import qts.runtime.execution_report_handler as handler_module
from qts.execution.order_manager import OrderManager
from qts.runtime.execution_report_handler import ExecutionReportHandler


def test_handler_module_does_not_import_apply_fill() -> None:
    source = inspect.getsource(handler_module)
    assert "ApplyFill" not in source


def test_handler_holds_no_account_actor_reference() -> None:
    handler = ExecutionReportHandler(order_manager=OrderManager(), account_id=None)
    attribute_names = list(vars(handler))
    assert not any("account_ref" in name for name in attribute_names)
    assert not any("_account_actor" in name for name in attribute_names)


def test_handler_returns_fills_for_actor_routing() -> None:
    # The handle() contract returns fills; routing to the account actor is the
    # caller's (OrderManagerActor's) responsibility, not the handler's.
    signature = inspect.signature(ExecutionReportHandler.handle)
    assert "report" in signature.parameters
    return_annotation = signature.return_annotation
    assert "OrderFill" in str(return_annotation)
