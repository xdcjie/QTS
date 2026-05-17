"""Anchor: replaying older-schema events runs them through a migration registry.

Domain fact: once an event is persisted, its payload version is durable;
schema evolution must preserve replay determinism. The event store reader
applies registered migrations keyed by ``(kind, from_version)`` before
yielding events.

Owner: ``qts.runtime.event_store.SchemaMigrationRegistry``.

Forbidden shortcut: ad-hoc ``if event.kind == X and v == '0':`` branches
inside readers; silent passthrough of unknown versions.
"""

from __future__ import annotations

from typing import Any

import pytest
from qts.runtime.event_store import (
    InMemoryEventStore,
    SchemaMigrationMissing,
    SchemaMigrationRegistry,
)
from qts.runtime.sinks.base import RuntimeEvent


def test_registered_migration_runs_during_replay() -> None:
    def migrate(payload: dict[str, Any]) -> dict[str, Any]:
        new_payload = dict(payload)
        new_payload["schema_audit"] = "migrated_v0_to_v1"
        return new_payload

    registry = SchemaMigrationRegistry()
    registry.register(
        kind="account.position_closed",
        from_version="0",
        to_version="1",
        migrate=migrate,
    )

    store = InMemoryEventStore(migration_registry=registry)
    legacy_event = RuntimeEvent(
        kind="account.position_closed",
        payload={"instrument_id": "EQUITY.US.NASDAQ.AAPL"},
        correlation_id=None,
        payload_schema_version="0",
    )
    store.append(legacy_event)

    replayed = store.replay()

    assert len(replayed) == 1
    migrated = replayed[0]
    assert isinstance(migrated, RuntimeEvent)
    assert migrated.payload_schema_version == "1"
    assert migrated.payload["schema_audit"] == "migrated_v0_to_v1"


def test_unknown_version_raises_schema_migration_missing() -> None:
    registry = SchemaMigrationRegistry()
    store = InMemoryEventStore(migration_registry=registry)
    legacy_event = RuntimeEvent(
        kind="unknown.legacy_kind",
        payload={"instrument_id": "EQUITY.US.NASDAQ.AAPL"},
        correlation_id=None,
        payload_schema_version="0",
    )
    store.append(legacy_event)

    with pytest.raises(SchemaMigrationMissing) as info:
        store.replay()
    assert "unknown.legacy_kind" in str(info.value)


def test_current_version_events_pass_through_unchanged() -> None:
    registry = SchemaMigrationRegistry()
    store = InMemoryEventStore(migration_registry=registry)
    current = RuntimeEvent(
        kind="runtime.snapshot",
        payload={"runtime_mode": "backtest"},
        payload_schema_version="1",
    )
    store.append(current)

    replayed = store.replay()
    assert len(replayed) == 1
    head = replayed[0]
    assert isinstance(head, RuntimeEvent)
    assert head.payload_schema_version == "1"


def test_chained_migrations_advance_through_intermediate_versions() -> None:
    def v0_to_v1(payload: dict[str, Any]) -> dict[str, Any]:
        new_payload = dict(payload)
        new_payload["stage"] = "v1"
        return new_payload

    def v1_to_v2(payload: dict[str, Any]) -> dict[str, Any]:
        new_payload = dict(payload)
        new_payload["stage"] = "v2"
        return new_payload

    registry = SchemaMigrationRegistry()
    registry.register(
        kind="account.position_closed", from_version="0", to_version="1", migrate=v0_to_v1
    )
    registry.register(
        kind="account.position_closed", from_version="1", to_version="2", migrate=v1_to_v2
    )

    store = InMemoryEventStore(migration_registry=registry)
    legacy = RuntimeEvent(
        kind="account.position_closed",
        payload={"instrument_id": "X"},
        payload_schema_version="0",
    )
    store.append(legacy)

    replayed = store.replay()
    head = replayed[0]
    assert isinstance(head, RuntimeEvent)
    assert head.payload_schema_version == "2"
    assert head.payload["stage"] == "v2"
