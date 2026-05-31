"""Operator pause via the control plane blocks new runtime orders.

QTS-FINAL-001: ``OperationsService.pause_runtime`` must pause the bound
``RuntimeSession`` so subsequent bars submit no new orders (reason
``RUNTIME_PAUSED``), proving the operator pause reaches the real runtime.
"""

from __future__ import annotations

from datetime import UTC, datetime

from qts.core.ids import OrderId
from qts.runtime.state import RuntimeSessionState

from tests.integration.test_live_kill_switch_flow import _bar
from tests.integration.test_operator_kill_switch_blocks_runtime_orders import build_operator_runtime


def test_operator_pause_blocks_new_orders() -> None:
    service, session, adapter = build_operator_runtime()
    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    paused = service.pause_runtime(operator_id="ops-a")
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))

    assert paused.state == "paused"
    assert session.state is RuntimeSessionState.PAUSED
    # No new order after the operator pause; only the pre-pause bar submitted.
    assert adapter.submitted_order_ids == [OrderId("live-000001")]
    assert blocked.reason_code == "RUNTIME_PAUSED"
