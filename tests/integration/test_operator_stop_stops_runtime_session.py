"""Operator stop via the control plane stops the bound runtime session.

QTS-FINAL-001: ``OperationsService.stop_runtime`` must stop the bound
``RuntimeSession`` so it leaves the running state and submits no further orders
(reason ``RUNTIME_NOT_RUNNING``), proving the operator stop reaches the runtime.
"""

from __future__ import annotations

from datetime import UTC, datetime

from qts.core.ids import OrderId
from qts.runtime.state import RuntimeSessionState

from tests.integration.test_live_kill_switch_flow import _bar
from tests.integration.test_operator_kill_switch_blocks_runtime_orders import build_operator_runtime


def test_operator_stop_stops_runtime_session() -> None:
    service, session, adapter = build_operator_runtime()
    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    stopped = service.stop_runtime(operator_id="ops-a", runtime_instance_id="ops-rt")
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))

    assert stopped.state == "stopped"
    assert session.state is RuntimeSessionState.STOPPED
    # No new order after the operator stop; only the pre-stop bar submitted.
    assert adapter.submitted_order_ids == [OrderId("live-000001")]
    assert blocked.reason_code == "RUNTIME_NOT_RUNNING"
