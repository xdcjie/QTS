"""State snapshot and recovery interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Serialized actor state snapshot envelope."""

    actor_id: str
    state_version: int
    payload: Any

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("actor_id must not be empty")
        if self.state_version < 0:
            raise ValueError("state_version must be non-negative")


class InMemorySnapshotStore:
    """In-memory snapshot store for deterministic tests and local recovery."""

    def __init__(self) -> None:
        self._snapshots: dict[str, StateSnapshot] = {}

    def save(self, snapshot: StateSnapshot) -> None:
        self._snapshots[snapshot.actor_id] = snapshot

    def load(self, actor_id: str) -> StateSnapshot | None:
        if not actor_id.strip():
            raise ValueError("actor_id must not be empty")
        return self._snapshots.get(actor_id)


__all__ = ["InMemorySnapshotStore", "StateSnapshot"]
