"""IBKR broker-order identity mapping."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from qts.core.hashing import stable_json_hash
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

    def snapshot_hash(self) -> str:
        """Return a deterministic hash for the durable order-map snapshot."""

        return stable_json_hash([self._record_payload(record) for record in self.snapshot()])

    @classmethod
    def restore(
        cls,
        snapshot: tuple[BrokerOrderRecord | Mapping[str, Any], ...],
    ) -> BrokerOrderMap:
        """Restore all lookup indexes from a broker-order-map snapshot."""

        order_map = cls()
        for item in snapshot:
            record = cls._coerce_record(item)
            order_map._store(record)
        return order_map

    def _store(self, record: BrokerOrderRecord) -> BrokerOrderRecord:
        existing = self._by_client_order_id.get(record.client_order_id)
        mapped_client = self._client_by_internal_order_id.get(record.internal_order_id)
        if mapped_client is not None and mapped_client != record.client_order_id:
            raise ValueError("internal_order_id already maps to a different client_order_id")
        if record.ibkr_order_id is not None:
            mapped_client = self._client_by_ibkr_order_id.get(record.ibkr_order_id)
            if mapped_client is not None and mapped_client != record.client_order_id:
                raise ValueError("ibkr_order_id already maps to a different client_order_id")
        if record.perm_id is not None:
            mapped_client = self._client_by_perm_id.get(record.perm_id)
            if mapped_client is not None and mapped_client != record.client_order_id:
                raise ValueError("perm_id already maps to a different client_order_id")
        if existing is not None:
            if existing.internal_order_id != record.internal_order_id:
                self._client_by_internal_order_id.pop(existing.internal_order_id, None)
            if (
                existing.ibkr_order_id != record.ibkr_order_id
                and existing.ibkr_order_id is not None
            ):
                self._client_by_ibkr_order_id.pop(existing.ibkr_order_id, None)
            if existing.perm_id != record.perm_id and existing.perm_id is not None:
                self._client_by_perm_id.pop(existing.perm_id, None)
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

    @staticmethod
    def _record_payload(record: BrokerOrderRecord) -> dict[str, object]:
        return {
            "internal_order_id": record.internal_order_id.value,
            "client_order_id": record.client_order_id,
            "account_id": record.account_id.value,
            "strategy_id": None if record.strategy_id is None else record.strategy_id.value,
            "submitted_at": record.submitted_at.isoformat(),
            "ibkr_order_id": record.ibkr_order_id,
            "perm_id": record.perm_id,
            "status": record.status,
            "last_broker_status_at": (
                None
                if record.last_broker_status_at is None
                else record.last_broker_status_at.isoformat()
            ),
        }

    @classmethod
    def _coerce_record(
        cls,
        item: BrokerOrderRecord | Mapping[str, Any],
    ) -> BrokerOrderRecord:
        if isinstance(item, BrokerOrderRecord):
            return item
        if not isinstance(item, Mapping):
            raise TypeError("broker order snapshot items must be BrokerOrderRecord or mapping")
        return BrokerOrderRecord(
            internal_order_id=cls._required_order_id(item, "internal_order_id"),
            client_order_id=cls._required_str(item, "client_order_id"),
            account_id=cls._required_account_id(item, "account_id"),
            strategy_id=cls._optional_strategy_id(item.get("strategy_id")),
            submitted_at=cls._required_datetime(item, "submitted_at"),
            ibkr_order_id=cls._optional_str(item.get("ibkr_order_id"), "ibkr_order_id"),
            perm_id=cls._optional_str(item.get("perm_id"), "perm_id"),
            status=cls._optional_str(item.get("status"), "status") or "pending_submission",
            last_broker_status_at=cls._optional_datetime(item.get("last_broker_status_at")),
        )

    @staticmethod
    def _required_str(item: Mapping[str, Any], field: str) -> str:
        if field not in item:
            raise ValueError(f"{field} is required")
        value = item[field]
        if not isinstance(value, str):
            raise TypeError(f"{field} must be a string")
        if not value.strip():
            raise ValueError(f"{field} must not be empty")
        return value

    @classmethod
    def _required_order_id(cls, item: Mapping[str, Any], field: str) -> OrderId:
        value = item.get(field)
        if isinstance(value, OrderId):
            return value
        return OrderId(cls._required_str(item, field))

    @classmethod
    def _required_account_id(cls, item: Mapping[str, Any], field: str) -> AccountId:
        value = item.get(field)
        if isinstance(value, AccountId):
            return value
        return AccountId(cls._required_str(item, field))

    @staticmethod
    def _optional_strategy_id(value: object) -> StrategyId | None:
        if value is None:
            return None
        if isinstance(value, StrategyId):
            return value
        if isinstance(value, str):
            return StrategyId(value)
        raise TypeError("strategy_id must be a string when provided")

    @staticmethod
    def _optional_str(value: object, field: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{field} must be a string when provided")
        if not value.strip():
            raise ValueError(f"{field} must not be empty when provided")
        return value

    @classmethod
    def _required_datetime(cls, item: Mapping[str, Any], field: str) -> datetime:
        if field not in item:
            raise ValueError(f"{field} is required")
        return cls._coerce_datetime(item[field], field)

    @classmethod
    def _optional_datetime(cls, value: object) -> datetime | None:
        if value is None:
            return None
        return cls._coerce_datetime(value, "last_broker_status_at")

    @staticmethod
    def _coerce_datetime(value: object, field: str) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise TypeError(f"{field} must be a datetime or ISO datetime string")


__all__ = ["BrokerOrderMap", "BrokerOrderRecord"]
