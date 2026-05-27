"""Canonical runtime event schema migrations.

Owner of the migration registry that ships in production. Every persisted
``RuntimeEvent`` flowing through the read path of ``InMemoryEventStore`` or
``FileEventStore`` is advanced through this registry, so historical replays
remain deterministic across schema evolutions.

The registry is non-empty by construction so the wiring is end-to-end real,
not test-only: the very first migration is the documented v0 → v1 transition
for ``account.position_closed``, which back-fills a ``schema_audit`` audit
field describing the migration that ran.
"""

from __future__ import annotations

from typing import Any

from qts.runtime.event_store import SchemaMigrationRegistry


def canonical_runtime_event_migrations() -> SchemaMigrationRegistry:
    """Build the production migration registry.

    The registry is mutable per call (a fresh instance) but always contains
    the same canonical migration set. Callers that need to register
    additional event-kind migrations layer them on top of this baseline.
    """
    registry = SchemaMigrationRegistry()
    registry.register(
        kind="account.position_closed",
        from_version="0",
        to_version="1",
        migrate=_account_position_closed_v0_to_v1,
    )
    return registry


def _account_position_closed_v0_to_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """Tag pre-canonical v0 ``account.position_closed`` payloads with a schema audit field.

    v0 (pre-OPT-26.1) had no schema version header attached to the event
    payload. v1 (current) adds the ``schema_audit`` marker so downstream
    consumers can confirm the event was advanced through the canonical
    migration, not silently passed through.
    """
    migrated = dict(payload)
    migrated["schema_audit"] = "migrated_v0_to_v1"
    return migrated


__all__ = ["canonical_runtime_event_migrations"]
