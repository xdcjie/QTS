"""IBKR broker-order identity mapping."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from qts.core.ids import AccountId, OrderId, StrategyId


@dataclass(frozen=True, slots=True)
class BrokerOrderRecord:
    """Audit record linking internal and IBKR order identifiers."""

    internal_order_id: OrderId
    client_order_id: str
    account_id: AccountId
    strategy_id: StrategyId | None
    submitted_at: datetime
    ibkr_order_id: str | None = None
    perm_id: str | None = None
    status: str = "pending_submission"
    last_broker_status_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        if self.ibkr_order_id is not None and not self.ibkr_order_id.strip():
            raise ValueError("ibkr_order_id must not be empty when provided")
        if self.perm_id is not None and not self.perm_id.strip():
            raise ValueError("perm_id must not be empty when provided")
        if not self.status.strip():
            raise ValueError("status must not be empty")


class BrokerOrderMap:
    """Owns lookup indexes across internal, client, broker, and permanent ids."""

    def __init__(self) -> None:
        self._by_client_order_id: dict[str, BrokerOrderRecord] = {}
        self._client_by_ibkr_order_id: dict[str, str] = {}
        self._client_by_perm_id: dict[str, str] = {}
        self._client_by_internal_order_id: dict[OrderId, str] = {}

    def record_pending_submission(
        self,
        *,
        internal_order_id: OrderId,
        client_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId | None = None,
        submitted_at: datetime,
    ) -> BrokerOrderRecord:
        """Record an order before the IBKR broker order id is known."""

        if client_order_id in self._by_client_order_id:
            record = self._by_client_order_id[client_order_id]
            if (
                record.internal_order_id != internal_order_id
                or record.account_id != account_id
                or record.strategy_id != strategy_id
            ):
                raise ValueError("client_order_id already maps to a different order route")
            return record
        record = BrokerOrderRecord(
            internal_order_id=internal_order_id,
            client_order_id=client_order_id,
            account_id=account_id,
            strategy_id=strategy_id,
            submitted_at=submitted_at,
        )
        self._store(record)
        return record

    def attach_ibkr_order_id(
        self,
        *,
        client_order_id: str,
        ibkr_order_id: str,
    ) -> BrokerOrderRecord:
        """Attach the broker order id returned by IBKR order submission."""

        record = self._require_client_order_id(client_order_id)
        return self._store(replace(record, ibkr_order_id=ibkr_order_id))

    def attach_perm_id(self, *, ibkr_order_id: str, perm_id: str) -> BrokerOrderRecord:
        """Attach IBKR's permanent id from order callbacks."""

        record = self.by_ibkr_order_id(ibkr_order_id)
        return self._store(replace(record, perm_id=perm_id))

    def mark_status(
        self,
        *,
        ibkr_order_id: str,
        status: str,
        last_broker_status_at: datetime,
    ) -> BrokerOrderRecord:
        """Record the latest broker status for audit and reconciliation."""

        record = self.by_ibkr_order_id(ibkr_order_id)
        return self._store(
            replace(record, status=status, last_broker_status_at=last_broker_status_at)
        )

    def by_client_order_id(self, client_order_id: str) -> BrokerOrderRecord:
        """Look up a record by client order id."""

        return self._require_client_order_id(client_order_id)

    def by_internal_order_id(self, internal_order_id: OrderId) -> BrokerOrderRecord:
        """Look up a record by internal order id."""

        return self._by_client_order_id[self._client_by_internal_order_id[internal_order_id]]

    def by_ibkr_order_id(self, ibkr_order_id: str) -> BrokerOrderRecord:
        """Look up a record by IBKR order id."""

        return self._by_client_order_id[self._client_by_ibkr_order_id[ibkr_order_id]]

    def by_perm_id(self, perm_id: str) -> BrokerOrderRecord:
        """Look up a record by IBKR permanent id."""

        return self._by_client_order_id[self._client_by_perm_id[perm_id]]

    def snapshot(self) -> tuple[BrokerOrderRecord, ...]:
        """Return a deterministic snapshot suitable for durable recovery."""

        return tuple(
            self._by_client_order_id[client_order_id]
            for client_order_id in sorted(self._by_client_order_id)
        )

    @classmethod
    def restore(cls, snapshot: tuple[BrokerOrderRecord, ...]) -> BrokerOrderMap:
        """Restore all lookup indexes from a broker-order-map snapshot."""

        order_map = cls()
        for record in snapshot:
            order_map._store(record)
        return order_map

    def _store(self, record: BrokerOrderRecord) -> BrokerOrderRecord:
        self._by_client_order_id[record.client_order_id] = record
        self._client_by_internal_order_id[record.internal_order_id] = record.client_order_id
        if record.ibkr_order_id is not None:
            self._client_by_ibkr_order_id[record.ibkr_order_id] = record.client_order_id
        if record.perm_id is not None:
            self._client_by_perm_id[record.perm_id] = record.client_order_id
        return record

    def _require_client_order_id(self, client_order_id: str) -> BrokerOrderRecord:
        if not client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        return self._by_client_order_id[client_order_id]


__all__ = ["BrokerOrderMap", "BrokerOrderRecord"]
