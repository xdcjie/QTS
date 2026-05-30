"""Account query application service.

Backs the account API route with the real account state source
(:class:`AccountSnapshot`, produced by ``AccountActor``) instead of a route
literal. When no account source is bound for the requested account the empty
cash projection is *derived* from the absence of a snapshot, not substituted
in the route.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from qts.application.dto.control_plane import AccountSnapshotDTO
from qts.portfolio.account_snapshot import AccountSnapshot


class AccountSnapshotSource(Protocol):
    """Read-only source of the current account snapshot."""

    def snapshot(self) -> AccountSnapshot:
        """Return the current account snapshot."""
        ...


class AccountQueryService:
    """Resolve account snapshots from bound per-account state sources."""

    def __init__(self, sources: Mapping[str, AccountSnapshotSource] | None = None) -> None:
        """Create the service over account-id-keyed snapshot sources."""
        self._sources = dict(sources or {})

    def account_snapshot(self, account_id: str) -> AccountSnapshotDTO:
        """Return an account snapshot, or a derived empty snapshot."""
        source = self._sources.get(account_id)
        if source is None:
            return AccountSnapshotDTO(account_id=account_id, cash={})
        snapshot = source.snapshot()
        return AccountSnapshotDTO(
            account_id=account_id,
            cash={currency: str(balance) for currency, balance in snapshot.cash.items()},
        )


__all__ = ["AccountQueryService", "AccountSnapshotSource"]
