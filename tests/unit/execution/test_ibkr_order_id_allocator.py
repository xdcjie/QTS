from __future__ import annotations

from pathlib import Path


def test_order_id_allocator_survives_restart_and_reconciles_by_client_id(tmp_path: Path) -> None:
    from qts.execution.adapters.ibkr_order_ids import IbkrOrderIdAllocator

    store_path = tmp_path / "ibkr-order-ids.json"
    allocator = IbkrOrderIdAllocator(store_path)
    allocator.reconcile_next_valid_id(client_id=201, broker_next_valid_id=100)

    assert allocator.allocate(client_id=201) == 100
    assert allocator.allocate(client_id=201) == 101

    restarted = IbkrOrderIdAllocator(store_path)
    restarted.reconcile_next_valid_id(client_id=201, broker_next_valid_id=50)
    restarted.reconcile_next_valid_id(client_id=202, broker_next_valid_id=7)

    assert restarted.allocate(client_id=201) == 102
    assert restarted.allocate(client_id=202) == 7
