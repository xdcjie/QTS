from __future__ import annotations

from datetime import UTC, datetime

import pytest


def _submitted_at(second: int = 0) -> datetime:
    return datetime(2026, 5, 14, 12, 0, second, tzinfo=UTC)


def test_perm_id_maps_to_internal_order() -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    submitted_at = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)
    order_map = BrokerOrderMap()

    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="ord-001",
        account_id=AccountId("acct-001"),
        strategy_id=StrategyId("strategy-001"),
        submitted_at=submitted_at,
    )
    order_map.attach_ibkr_order_id(client_order_id="ord-001", ibkr_order_id="100")
    order_map.attach_perm_id(ibkr_order_id="100", perm_id="99001")

    record = order_map.by_perm_id("99001")

    assert record.internal_order_id == OrderId("ord-001")
    assert record.client_order_id == "ord-001"
    assert record.ibkr_order_id == "100"
    assert record.perm_id == "99001"
    assert record.account_id == AccountId("acct-001")
    assert record.strategy_id == StrategyId("strategy-001")


def test_duplicate_client_order_id_with_different_route_fails() -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    submitted_at = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)
    order_map = BrokerOrderMap()

    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-001",
        account_id=AccountId("acct-001"),
        strategy_id=StrategyId("strategy-001"),
        submitted_at=submitted_at,
    )

    with pytest.raises(ValueError, match="client_order_id already maps"):
        order_map.record_pending_submission(
            internal_order_id=OrderId("ord-002"),
            client_order_id="client-001",
            account_id=AccountId("acct-001"),
            strategy_id=StrategyId("strategy-001"),
            submitted_at=submitted_at,
        )


def test_broker_order_map_snapshot_round_trips_all_indexes() -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    submitted_at = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-001",
        account_id=AccountId("acct-001"),
        strategy_id=StrategyId("strategy-001"),
        submitted_at=submitted_at,
    )
    order_map.attach_ibkr_order_id(client_order_id="client-001", ibkr_order_id="100")
    order_map.attach_perm_id(ibkr_order_id="100", perm_id="99001")

    restored = BrokerOrderMap.restore(order_map.snapshot())

    assert restored.by_internal_order_id(OrderId("ord-001")).client_order_id == "client-001"
    assert restored.by_ibkr_order_id("100").internal_order_id == OrderId("ord-001")
    assert restored.by_perm_id("99001").strategy_id == StrategyId("strategy-001")


def test_broker_order_map_restore_preserves_callback_ownership_indexes() -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    order_map = BrokerOrderMap()
    pending = order_map.record_pending_submission(
        internal_order_id=OrderId("ord-pending"),
        client_order_id="client-pending",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-alpha"),
        submitted_at=_submitted_at(1),
    )
    submitted = order_map.record_pending_submission(
        internal_order_id=OrderId("ord-submitted"),
        client_order_id="client-submitted",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-alpha"),
        submitted_at=_submitted_at(2),
    )
    order_map.attach_ibkr_order_id(
        client_order_id=submitted.client_order_id,
        ibkr_order_id="101",
    )
    order_map.attach_perm_id(ibkr_order_id="101", perm_id="99001")
    order_map.mark_status(
        ibkr_order_id="101",
        status="Submitted",
        last_broker_status_at=_submitted_at(3),
    )
    filled = order_map.record_pending_submission(
        internal_order_id=OrderId("ord-filled"),
        client_order_id="client-filled",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-beta"),
        submitted_at=_submitted_at(4),
    )
    order_map.attach_ibkr_order_id(client_order_id=filled.client_order_id, ibkr_order_id="102")
    order_map.attach_perm_id(ibkr_order_id="102", perm_id="99002")
    order_map.mark_status(
        ibkr_order_id="102",
        status="Filled",
        last_broker_status_at=_submitted_at(5),
    )
    cancelled = order_map.record_pending_submission(
        internal_order_id=OrderId("ord-cancelled"),
        client_order_id="client-cancelled",
        account_id=AccountId("acct-ibkr"),
        strategy_id=None,
        submitted_at=_submitted_at(6),
    )
    order_map.attach_ibkr_order_id(
        client_order_id=cancelled.client_order_id,
        ibkr_order_id="103",
    )
    order_map.attach_perm_id(ibkr_order_id="103", perm_id="99003")
    order_map.mark_status(
        ibkr_order_id="103",
        status="Cancelled",
        last_broker_status_at=_submitted_at(7),
    )

    restored = BrokerOrderMap.restore(order_map.snapshot())

    assert restored.snapshot() == order_map.snapshot()
    assert restored.by_client_order_id(pending.client_order_id).internal_order_id == OrderId(
        "ord-pending"
    )
    open_order_owner = restored.by_client_order_id("client-submitted")
    execution_owner = restored.by_ibkr_order_id("102")
    commission_owner = restored.by_perm_id("99002")
    cancelled_owner = restored.by_internal_order_id(OrderId("ord-cancelled"))
    assert open_order_owner.account_id == AccountId("acct-ibkr")
    assert open_order_owner.strategy_id == StrategyId("strategy-alpha")
    assert open_order_owner.status == "Submitted"
    assert execution_owner.client_order_id == "client-filled"
    assert commission_owner.internal_order_id == OrderId("ord-filled")
    assert commission_owner.strategy_id == StrategyId("strategy-beta")
    assert cancelled_owner.ibkr_order_id == "103"
    assert cancelled_owner.perm_id == "99003"
    assert cancelled_owner.status == "Cancelled"


def test_broker_order_map_snapshot_hash_is_deterministic() -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    first = BrokerOrderMap()
    second = BrokerOrderMap()
    for order_map, client_ids in (
        (first, ("client-b", "client-a")),
        (second, ("client-a", "client-b")),
    ):
        for client_order_id in client_ids:
            suffix = client_order_id[-1]
            numeric_suffix = "1" if suffix == "a" else "2"
            order_map.record_pending_submission(
                internal_order_id=OrderId(f"ord-{suffix}"),
                client_order_id=client_order_id,
                account_id=AccountId("acct-ibkr"),
                strategy_id=StrategyId("strategy-alpha"),
                submitted_at=_submitted_at(int(numeric_suffix)),
            )
            order_map.attach_ibkr_order_id(
                client_order_id=client_order_id,
                ibkr_order_id=f"10{numeric_suffix}",
            )
            order_map.attach_perm_id(
                ibkr_order_id=f"10{numeric_suffix}",
                perm_id=f"9900{numeric_suffix}",
            )

    assert first.snapshot() == second.snapshot()
    assert first.snapshot_hash() == second.snapshot_hash()
    assert first.snapshot_hash().startswith("sha256:")


def test_broker_order_map_restore_fails_fast_without_client_order_id() -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    payload = {
        "internal_order_id": OrderId("ord-001"),
        "account_id": AccountId("acct-ibkr"),
        "strategy_id": StrategyId("strategy-alpha"),
        "submitted_at": _submitted_at(),
        "ibkr_order_id": "100",
        "perm_id": "99001",
        "status": "Submitted",
        "last_broker_status_at": _submitted_at(1),
    }

    with pytest.raises(ValueError, match="client_order_id is required"):
        BrokerOrderMap.restore((payload,))


def test_broker_order_map_restore_fails_fast_on_ambiguous_broker_identity() -> None:
    from dataclasses import replace

    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord-001"),
        client_order_id="client-001",
        account_id=AccountId("acct-ibkr"),
        strategy_id=StrategyId("strategy-alpha"),
        submitted_at=_submitted_at(),
    )
    order_map.attach_ibkr_order_id(client_order_id="client-001", ibkr_order_id="100")
    first = order_map.by_client_order_id("client-001")
    second = replace(
        first,
        internal_order_id=OrderId("ord-002"),
        client_order_id="client-002",
    )

    with pytest.raises(ValueError, match="ibkr_order_id already maps"):
        BrokerOrderMap.restore((order_map.by_client_order_id("client-001"), second))
