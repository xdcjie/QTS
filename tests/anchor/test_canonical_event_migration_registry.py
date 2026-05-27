"""Anchor: production code ships a non-empty SchemaMigrationRegistry.

Domain fact: an event store that ships with an empty migration registry is
dead infrastructure — anchor tests prove the registry contract but no real
schema evolution path is exercised. Production code must register at least
one real migration so the wiring is end-to-end real, not test-only.

Owner: ``qts.runtime.event_migrations.canonical_runtime_event_migrations``
and ``InMemoryEventStore`` default constructor.

Forbidden shortcut: returning ``SchemaMigrationRegistry()`` from production
factories; treating migration plumbing as test-only.
"""

from __future__ import annotations

from qts.runtime.event_migrations import canonical_runtime_event_migrations
from qts.runtime.event_store import InMemoryEventStore
from qts.runtime.sinks.base import RuntimeEvent


def test_canonical_registry_has_at_least_one_real_migration() -> None:
    registry = canonical_runtime_event_migrations()
    assert registry.size() >= 1
    assert ("account.position_closed", "0") in registry.registered_keys()


def test_default_in_memory_event_store_uses_canonical_registry() -> None:
    store = InMemoryEventStore()
    historical_event = RuntimeEvent(
        kind="account.position_closed",
        payload={"instrument_id": "EQUITY.US.NASDAQ.AAPL"},
        payload_schema_version="0",
    )
    store.append(historical_event)

    replayed = store.replay()
    assert len(replayed) == 1
    head = replayed[0]
    assert isinstance(head, RuntimeEvent)
    assert head.payload_schema_version == "1"
    assert head.payload["schema_audit"] == "migrated_v0_to_v1"


def test_event_with_unknown_historical_version_still_raises() -> None:
    import pytest
    from qts.runtime.event_store import SchemaMigrationMissing

    store = InMemoryEventStore()
    historical = RuntimeEvent(
        kind="runtime.unknown_event_kind",
        payload={},
        payload_schema_version="0",
    )
    store.append(historical)
    with pytest.raises(SchemaMigrationMissing):
        store.replay()
