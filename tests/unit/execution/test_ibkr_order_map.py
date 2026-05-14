from __future__ import annotations

from datetime import UTC, datetime


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
