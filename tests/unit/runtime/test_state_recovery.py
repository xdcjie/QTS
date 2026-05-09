from __future__ import annotations

from decimal import Decimal


def test_in_memory_snapshot_store_saves_and_restores_actor_state() -> None:
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.state_recovery import InMemorySnapshotStore, StateSnapshot

    actor = AccountActor(initial_cash={"USD": Decimal("10000")})
    snapshot = StateSnapshot(
        actor_id="account:acct-001",
        state_version=1,
        payload=actor.snapshot(),
    )
    store = InMemorySnapshotStore()

    store.save(snapshot)

    assert store.load("account:acct-001") == snapshot
