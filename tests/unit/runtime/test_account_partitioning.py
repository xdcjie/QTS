from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, BrokerId, InstrumentId
from qts.runtime.partitioning import AccountBrokerMapping, AccountPartitionPolicy, AccountRiskConfig


def test_account_partitioning_uses_internal_account_id_and_keeps_broker_id_boundary_only() -> None:
    policy = AccountPartitionPolicy()
    mapping = AccountBrokerMapping(
        account_id=AccountId("acct-a"),
        broker_id=BrokerId("ibkr-paper"),
        broker_account_id="DU12345",
    )
    risk_config = AccountRiskConfig(
        account_id=AccountId("acct-a"),
        max_order_notional=Decimal("10000"),
        instrument_limits={InstrumentId("EQUITY.US.NASDAQ.AAPL"): Decimal("5000")},
    )

    assert policy.partition_for(AccountId("acct-a")) == "account:acct-a"
    assert mapping.boundary_payload() == {"broker_id": "ibkr-paper", "broker_account_id": "DU12345"}
    assert risk_config.limit_for(InstrumentId("EQUITY.US.NASDAQ.AAPL")) == Decimal("5000")
    assert risk_config.limit_for(InstrumentId("EQUITY.US.NASDAQ.MSFT")) == Decimal("10000")
