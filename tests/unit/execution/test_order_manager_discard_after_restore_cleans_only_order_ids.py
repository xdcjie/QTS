"""QTS-FINAL-006: discard after restore removes only the discarded order's ids.

After a snapshot/restore round-trip, compacting one terminal order must remove
exactly that order's fill/report ids from the global idempotency sets and leave
ids owned by other (still active/restored) orders intact.
"""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
)
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import OrderManager


def _fill_one_order(manager: OrderManager, *, order_id: str, broker_id: str) -> None:
    manager.create_order(
        OrderIntent(
            order_id=OrderId(order_id),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("10"),
        ),
        risk_decision=RiskDecision.approve(),
    )
    manager.mark_sent(OrderId(order_id), broker_order_id=broker_id)
    manager.process_report(
        ExecutionReport(
            report_id=f"rpt-{order_id}",
            broker_order_id=broker_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=Decimal("10"),
            fill_price=Decimal("100"),
            fill_id=f"fill-{order_id}",
        )
    )


def test_discard_after_restore_cleans_only_discarded_order_ids() -> None:
    manager = OrderManager()
    _fill_one_order(manager, order_id="ord-001", broker_id="broker-001")
    _fill_one_order(manager, order_id="ord-002", broker_id="broker-002")

    restored = OrderManager.restore(manager.snapshot())

    restored.discard_terminal_order(OrderId("ord-001"))
    after = restored.snapshot()

    # ord-001's ids are gone from the global sets; ord-002's are preserved.
    assert "fill-ord-001" not in after.seen_fill_ids
    assert "rpt-ord-001" not in after.seen_report_ids
    assert "fill-ord-002" in after.seen_fill_ids
    assert "rpt-ord-002" in after.seen_report_ids

    # The per-order map for the surviving order is intact; the discarded one gone.
    fill_map = dict(after.fill_ids_by_order)
    assert OrderId("ord-001") not in fill_map
    assert fill_map[OrderId("ord-002")] == ("fill-ord-002",)


def test_restored_order_fill_ownership_is_re_emittable_into_a_new_snapshot() -> None:
    manager = OrderManager()
    _fill_one_order(manager, order_id="ord-001", broker_id="broker-001")
    restored = OrderManager.restore(manager.snapshot())

    # The restored manager still owns ord-001's ids, so discarding it compacts
    # them rather than leaving them orphaned in the global set (the bug this
    # issue closes: restore previously reset the per-order maps to empty).
    restored.discard_terminal_order(OrderId("ord-001"))
    after = restored.snapshot()

    assert after.seen_fill_ids == ()
    assert after.seen_report_ids == ()
