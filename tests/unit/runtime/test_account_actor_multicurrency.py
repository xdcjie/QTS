"""Gate tests for multi-currency account snapshot fidelity (DR-032)."""

from __future__ import annotations

from decimal import Decimal

from qts.runtime.actors.account_actor import AccountActor


def test_snapshot_exports_all_currency_balances() -> None:
    actor = AccountActor(initial_cash={"USD": Decimal("1000"), "EUR": Decimal("500")})
    snapshot = actor.snapshot()
    assert snapshot.cash["USD"] == Decimal("1000")
    assert snapshot.cash["EUR"] == Decimal("500")


def test_restore_preserves_all_currency_balances() -> None:
    actor = AccountActor(initial_cash={"USD": Decimal("1000"), "EUR": Decimal("500")})
    restored = AccountActor.restore(actor.snapshot())
    restored_snapshot = restored.snapshot()
    assert restored_snapshot.cash["USD"] == Decimal("1000")
    assert restored_snapshot.cash["EUR"] == Decimal("500")
