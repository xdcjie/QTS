"""Persistent IBKR order-id allocation."""

from __future__ import annotations

import json
from pathlib import Path


class IbkrOrderIdAllocator:
    """Allocates non-reused IBKR order ids per IBKR client id."""

    def __init__(self, store_path: str | Path | None = None) -> None:
        self._store_path = Path(store_path) if store_path is not None else None
        self._next_ids: dict[int, int] = {}
        self._load()

    def reconcile_next_valid_id(self, *, client_id: int, broker_next_valid_id: int) -> None:
        """Merge Gateway nextValidId without moving the local cursor backward."""

        self._validate_client_id(client_id)
        if broker_next_valid_id <= 0:
            raise ValueError("broker_next_valid_id must be positive")
        self._next_ids[client_id] = max(self._next_ids.get(client_id, 0), broker_next_valid_id)
        self._persist()

    def allocate(self, *, client_id: int) -> int:
        """Return the next order id for a client id and persist the advanced cursor."""

        self._validate_client_id(client_id)
        order_id = self._next_ids.get(client_id)
        if order_id is None:
            raise RuntimeError("IBKR nextValidId has not been reconciled for client_id")
        self._next_ids[client_id] = order_id + 1
        self._persist()
        return order_id

    def next_id(self, *, client_id: int) -> int | None:
        """Return the current next id for display and readiness checks."""

        self._validate_client_id(client_id)
        return self._next_ids.get(client_id)

    def snapshot(self) -> dict[int, int]:
        """Return a stable snapshot of allocated client-id cursors."""

        return dict(sorted(self._next_ids.items()))

    def _load(self) -> None:
        if self._store_path is None or not self._store_path.exists():
            return
        payload = json.loads(self._store_path.read_text(encoding="utf-8"))
        self._next_ids = {
            int(client_id): int(next_id) for client_id, next_id in payload["next_ids"].items()
        }

    def _persist(self) -> None:
        if self._store_path is None:
            return
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"next_ids": {str(key): value for key, value in sorted(self._next_ids.items())}}
        self._store_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _validate_client_id(client_id: int) -> None:
        if client_id <= 0:
            raise ValueError("client_id must be positive")


__all__ = ["IbkrOrderIdAllocator"]
