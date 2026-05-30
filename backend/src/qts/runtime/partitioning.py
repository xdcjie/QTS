"""Account partitioning and live broker boundary mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qts.core.ids import AccountId, BrokerId, InstrumentId


class AccountPartitionPolicy:
    """Partition live state and messages by internal account id."""

    def partition_for(self, account_id: AccountId) -> str:
        """Return the partition key for the given account."""
        return f"account:{account_id.value}"


@dataclass(frozen=True, slots=True)
class AccountBrokerMapping:
    """Boundary-only broker account mapping."""

    account_id: AccountId
    broker_id: BrokerId
    broker_account_id: str

    def __post_init__(self) -> None:
        """Require a non-empty broker account id."""
        if not self.broker_account_id.strip():
            raise ValueError("broker_account_id must not be empty")

    def boundary_payload(self) -> dict[str, str]:
        """Serialize the broker id and account id for the broker boundary."""
        return {
            "broker_id": self.broker_id.value,
            "broker_account_id": self.broker_account_id,
        }


@dataclass(frozen=True, slots=True)
class AccountRiskConfig:
    """Per-account live risk limits."""

    account_id: AccountId
    max_order_notional: Decimal
    instrument_limits: dict[InstrumentId, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Require a positive max notional and positive per-instrument limits."""
        if self.max_order_notional <= Decimal("0"):
            raise ValueError("max_order_notional must be positive")
        if any(limit <= Decimal("0") for limit in self.instrument_limits.values()):
            raise ValueError("instrument limits must be positive")

    def limit_for(self, instrument_id: InstrumentId) -> Decimal:
        """Return the notional limit for the instrument, or the account default."""
        return self.instrument_limits.get(instrument_id, self.max_order_notional)


__all__ = ["AccountBrokerMapping", "AccountPartitionPolicy", "AccountRiskConfig"]
