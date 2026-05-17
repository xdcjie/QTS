"""Durable account recovery — wires DurableSnapshotStore + SnapshotFrequencyPolicy.

Holds an append-only snapshot store and a cadence policy, persists
``AccountActor`` snapshots when the policy says yes, and rehydrates a
fresh actor from the latest persisted snapshot on startup.

This is the production caller that closes the OPT-64 wiring gap. The
existing ``AccountActor.snapshot`` / ``AccountActor.restore`` round-trip
provides byte-identical state recovery; this module is the only layer
that touches the durable store.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import AccountId, InstrumentId
from qts.portfolio.cash_book import CashBook
from qts.portfolio.holdings import Holding, HoldingBook
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.state_recovery import (
    DurableSnapshotStore,
    SnapshotFrequencyPolicy,
    StateSnapshot,
)


@dataclass(slots=True)
class DurableAccountRecovery:
    """Coordinator for AccountActor snapshot persistence and recovery."""

    store: DurableSnapshotStore
    policy: SnapshotFrequencyPolicy
    _last_snapshot_event_count: int = 0

    def persist_if_due(
        self,
        actor: AccountActor,
        *,
        event_count: int,
        elapsed: timedelta,
    ) -> bool:
        """Persist a snapshot when the policy's cadence is reached.

        Returns ``True`` when a snapshot was written. The cadence is
        evaluated against events accumulated since the previous save, so
        a policy of ``every_event_count=3`` writes every third event.
        """
        events_since_last = event_count - self._last_snapshot_event_count
        if not self.policy.should_snapshot(event_count=events_since_last, elapsed=elapsed):
            return False
        snapshot = actor.snapshot()
        actor_id = self._actor_id(snapshot.account_id)
        self.store.save(
            StateSnapshot(
                actor_id=actor_id,
                state_version=event_count,
                payload=self._serialize_account_snapshot(snapshot),
                last_sequence=event_count,
            )
        )
        self._last_snapshot_event_count = event_count
        return True

    def restore_account(
        self,
        *,
        actor_id: str,
        initial_cash: Mapping[str, Decimal],
        account_id: AccountId,
    ) -> AccountActor:
        """Return an actor rehydrated from the latest snapshot, or a fresh one."""
        stored = self.store.load(actor_id)
        if stored is None:
            return AccountActor(initial_cash=initial_cash, account_id=account_id)
        return self._restore_from_payload(stored.payload, account_id=account_id)

    @staticmethod
    def _actor_id(account_id: AccountId | None) -> str:
        if account_id is None:
            return "account:default"
        return f"account:{account_id.value}"

    @staticmethod
    def _serialize_account_snapshot(snapshot: AccountSnapshot) -> dict[str, Any]:
        return {
            "account_id": None if snapshot.account_id is None else snapshot.account_id.value,
            "cash": {currency: str(balance) for currency, balance in snapshot.cash.items()},
            "holdings": {
                instrument_id.value: {
                    "quantity": str(holding.quantity),
                    "average_cost": str(holding.average_cost),
                    "realized_pnl": str(holding.realized_pnl),
                    "opened_at": (
                        None if holding.opened_at is None else holding.opened_at.isoformat()
                    ),
                    "last_fill_at": (
                        None if holding.last_fill_at is None else holding.last_fill_at.isoformat()
                    ),
                }
                for instrument_id, holding in snapshot.holdings.items()
            },
            "seen_fill_ids": list(snapshot.seen_fill_ids),
        }

    @classmethod
    def _restore_from_payload(
        cls,
        payload: dict[str, Any],
        *,
        account_id: AccountId,
    ) -> AccountActor:
        cash: dict[str, Decimal] = {
            currency: Decimal(str(balance))
            for currency, balance in dict(payload.get("cash", {})).items()
        }
        holdings: dict[InstrumentId, Holding] = {}
        for raw_instrument_id, raw_holding in dict(payload.get("holdings", {})).items():
            instrument_id = InstrumentId(str(raw_instrument_id))
            holdings[instrument_id] = Holding(
                instrument_id=instrument_id,
                quantity=Decimal(str(raw_holding["quantity"])),
                average_cost=Decimal(str(raw_holding["average_cost"])),
                realized_pnl=Decimal(str(raw_holding["realized_pnl"])),
                opened_at=cls._parse_optional_datetime(raw_holding.get("opened_at")),
                last_fill_at=cls._parse_optional_datetime(raw_holding.get("last_fill_at")),
            )
        actor = AccountActor(initial_cash=cash, account_id=account_id)
        actor._cash = CashBook(cash)
        actor._holdings = HoldingBook(holdings)
        seen_fill_ids = tuple(str(fill_id) for fill_id in payload.get("seen_fill_ids", ()))
        from qts.execution.idempotency import FillIdempotencyStore

        actor._fill_ids = FillIdempotencyStore.restore(seen_fill_ids)
        return actor

    @staticmethod
    def _parse_optional_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(str(value))


__all__ = ["DurableAccountRecovery"]
