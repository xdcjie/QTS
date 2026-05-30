"""QTS-FINAL-006: OrderManager snapshots round-trip per-order idempotency maps.

Recovery snapshots must preserve the ownership metadata (which fill/report ids
belong to which order) so a restored manager can later compact a terminal
order's ids without disturbing other orders.
"""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
    OrderStateSnapshot,
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


def test_snapshot_records_per_order_idempotency_maps() -> None:
    manager = OrderManager()
    _fill_one_order(manager, order_id="ord-001", broker_id="broker-001")

    snapshot = manager.snapshot()

    fill_map = dict(snapshot.fill_ids_by_order)
    report_map = dict(snapshot.report_ids_by_order)
    assert fill_map[OrderId("ord-001")] == ("fill-ord-001",)
    assert report_map[OrderId("ord-001")] == ("rpt-ord-001",)


def test_restore_round_trips_per_order_idempotency_maps() -> None:
    manager = OrderManager()
    _fill_one_order(manager, order_id="ord-001", broker_id="broker-001")
    _fill_one_order(manager, order_id="ord-002", broker_id="broker-002")

    restored = OrderManager.restore(manager.snapshot())

    # The restored manager reproduces the same snapshot, including the maps.
    assert restored.snapshot() == manager.snapshot()
    restored_fill_map = dict(restored.snapshot().fill_ids_by_order)
    assert restored_fill_map[OrderId("ord-001")] == ("fill-ord-001",)
    assert restored_fill_map[OrderId("ord-002")] == ("fill-ord-002",)


def test_legacy_snapshot_without_maps_restores_as_global_non_compactable() -> None:
    # A snapshot produced before per-order ownership existed has empty maps but
    # populated global seen sets. Restore must not invent ownership; the ids stay
    # in the global sets and are not removed when an order is discarded.
    legacy = OrderStateSnapshot(
        orders=(),
        broker_to_order=(),
        seen_fill_ids=("legacy-fill",),
        seen_report_ids=("legacy-report",),
    )

    restored = OrderManager.restore(legacy)
    round_tripped = restored.snapshot()

    assert round_tripped.seen_fill_ids == ("legacy-fill",)
    assert round_tripped.seen_report_ids == ("legacy-report",)
    assert round_tripped.fill_ids_by_order == ()
    assert round_tripped.report_ids_by_order == ()
