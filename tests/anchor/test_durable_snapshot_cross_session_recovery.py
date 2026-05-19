"""Anchor: cross-restart recovery via DurableSnapshotStore is byte-identical.

Domain fact: live trading and long-running paper sessions must survive a
restart. After OPT-64 the runtime ships
``qts.runtime.durable_recovery.DurableAccountRecovery``, a coordinator
that holds a ``DurableSnapshotStore`` + ``SnapshotFrequencyPolicy`` and
persists ``AccountActor`` snapshots at the configured cadence. A fresh
process can rehydrate from the latest snapshot and continue applying
remaining events to reach byte-identical final state.

Owner: ``qts.runtime.durable_recovery.DurableAccountRecovery``.

Forbidden shortcut: bypassing the existing snapshot/restore round-trip
on AccountActor; mocking the file store.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders import OrderFill, OrderSide
from qts.runtime.actors.account_actor import AccountActor, ApplyFill
from qts.runtime.durable_recovery import DurableAccountRecovery
from qts.runtime.state_recovery import DurableSnapshotStore, SnapshotFrequencyPolicy

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _fill(index: int, *, side: OrderSide, price: str) -> ApplyFill:
    return ApplyFill(
        fill=OrderFill(
            fill_id=f"f-{index}",
            order_id=OrderId(f"ord-{index}"),
            instrument_id=_INSTRUMENT,
            side=side,
            quantity=Decimal("1"),
            price=Decimal(price),
            account_id=AccountId("acct-1"),
        ),
        currency="USD",
        multiplier=Decimal("1"),
    )


def _continuous_run() -> AccountActor:
    actor = AccountActor(
        initial_cash={"USD": Decimal("100000")},
        account_id=AccountId("acct-1"),
    )
    for i in range(1, 7):
        side = OrderSide.BUY if i % 2 == 1 else OrderSide.SELL
        actor.handle(_fill(i, side=side, price="100"))
    return actor


def test_recovery_after_simulated_restart_reproduces_final_state(tmp_path: Path) -> None:
    store = DurableSnapshotStore(path=tmp_path / "snapshots.jsonl")
    recovery = DurableAccountRecovery(
        store=store,
        policy=SnapshotFrequencyPolicy(every_event_count=3),
    )

    # Phase 1: handle 3 fills, persist at the configured cadence, "crash".
    phase_one_actor = AccountActor(
        initial_cash={"USD": Decimal("100000")},
        account_id=AccountId("acct-1"),
    )
    for i in range(1, 4):
        side = OrderSide.BUY if i % 2 == 1 else OrderSide.SELL
        phase_one_actor.handle(_fill(i, side=side, price="100"))
        recovery.persist_if_due(phase_one_actor, event_count=i, elapsed=timedelta(0))

    # Phase 2: fresh actor restored from the persisted snapshot continues.
    phase_two_actor = recovery.restore_account(
        actor_id="account:acct-1",
        initial_cash={"USD": Decimal("100000")},
        account_id=AccountId("acct-1"),
    )
    for i in range(4, 7):
        side = OrderSide.BUY if i % 2 == 1 else OrderSide.SELL
        phase_two_actor.handle(_fill(i, side=side, price="100"))

    expected = _continuous_run()
    expected_snapshot = expected.snapshot()
    recovered_snapshot = phase_two_actor.snapshot()

    assert dict(recovered_snapshot.cash) == dict(expected_snapshot.cash)
    assert set(recovered_snapshot.holdings.keys()) == set(expected_snapshot.holdings.keys())
    for instrument_id, holding in expected_snapshot.holdings.items():
        actual = recovered_snapshot.holdings[instrument_id]
        assert actual.quantity == holding.quantity
        assert actual.average_cost == holding.average_cost
        assert actual.realized_pnl == holding.realized_pnl
    assert recovered_snapshot.seen_fill_ids == expected_snapshot.seen_fill_ids


def test_no_snapshot_returns_fresh_actor(tmp_path: Path) -> None:
    store = DurableSnapshotStore(path=tmp_path / "empty.jsonl")
    recovery = DurableAccountRecovery(
        store=store,
        policy=SnapshotFrequencyPolicy(every_event_count=3),
    )
    actor = recovery.restore_account(
        actor_id="account:acct-1",
        initial_cash={"USD": Decimal("50000")},
        account_id=AccountId("acct-1"),
    )
    snapshot = actor.snapshot()
    assert snapshot.cash["USD"] == Decimal("50000")
    assert dict(snapshot.holdings) == {}
