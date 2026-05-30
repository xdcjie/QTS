"""Read-only account snapshot value object owned by the portfolio layer.

The snapshot is a pure value object: it carries the account's cash balances and
holdings without any runtime, actor, or broker dependency. Lower layers (risk,
portfolio) and the runtime alike consume it, so it lives in the portfolio layer
beside ``Holding`` rather than in the runtime layer that produces it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId
from qts.portfolio.holdings import Holding


@dataclass(frozen=True, slots=True, init=False)
class AccountSnapshot:
    """Read-only account snapshot."""

    cash: Mapping[str, Decimal]
    holdings: Mapping[InstrumentId, Holding]
    account_id: AccountId | None = None
    seen_fill_ids: tuple[str, ...] = ()

    def __init__(
        self,
        *,
        cash: Mapping[str, Decimal],
        holdings: Mapping[InstrumentId, Holding] | None = None,
        positions: Mapping[InstrumentId, Holding] | None = None,
        account_id: AccountId | None = None,
        seen_fill_ids: tuple[str, ...] = (),
    ) -> None:
        object.__setattr__(self, "cash", cash)
        object.__setattr__(self, "holdings", holdings if holdings is not None else positions or {})
        object.__setattr__(self, "account_id", account_id)
        object.__setattr__(self, "seen_fill_ids", seen_fill_ids)

    @property
    def positions(self) -> Mapping[InstrumentId, Holding]:
        """Return holdings as quantity-bearing position snapshots."""
        return self.holdings


__all__ = ["AccountSnapshot"]
