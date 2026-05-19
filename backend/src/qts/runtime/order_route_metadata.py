"""Route and trace metadata for runtime order submission."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from qts.core.ids import AccountId, BrokerId, CorrelationId, StrategyId


@dataclass(frozen=True, slots=True)
class OrderRouteMetadata:
    """Route and trace metadata captured when an order is submitted."""

    broker_id: BrokerId
    account_id: AccountId
    strategy_id: StrategyId
    client_order_id: str
    correlation_id: CorrelationId
    contributing_strategy_ids: tuple[StrategyId, ...] = ()
    aggregation_decision_id: str | None = None

    def __post_init__(self) -> None:
        """Validate route and trace metadata."""
        if not self.client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        if self.aggregation_decision_id is not None and not self.aggregation_decision_id.strip():
            raise ValueError("aggregation_decision_id must not be empty")

    def to_payload(self) -> dict[str, str]:
        """Serialize route metadata for recovery snapshots."""
        payload = {
            "broker_id": self.broker_id.value,
            "account_id": self.account_id.value,
            "strategy_id": self.strategy_id.value,
            "client_order_id": self.client_order_id,
            "correlation_id": self.correlation_id.value,
        }
        if self.contributing_strategy_ids:
            payload["contributing_strategy_ids"] = ",".join(
                strategy_id.value for strategy_id in self.contributing_strategy_ids
            )
        if self.aggregation_decision_id is not None:
            payload["aggregation_decision_id"] = self.aggregation_decision_id
        return payload

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> OrderRouteMetadata:
        """Restore route metadata from a recovery snapshot payload."""
        raw_contributors = payload.get("contributing_strategy_ids", "")
        if isinstance(raw_contributors, str):
            contributing_strategy_ids = tuple(
                StrategyId(value) for value in raw_contributors.split(",") if value
            )
        elif isinstance(raw_contributors, Iterable):
            contributing_strategy_ids = tuple(StrategyId(str(value)) for value in raw_contributors)
        else:
            contributing_strategy_ids = ()
        return cls(
            broker_id=BrokerId(str(payload["broker_id"])),
            account_id=AccountId(str(payload["account_id"])),
            strategy_id=StrategyId(str(payload["strategy_id"])),
            client_order_id=str(payload["client_order_id"]),
            correlation_id=CorrelationId(str(payload["correlation_id"])),
            contributing_strategy_ids=contributing_strategy_ids,
            aggregation_decision_id=(
                str(payload["aggregation_decision_id"])
                if payload.get("aggregation_decision_id") is not None
                else None
            ),
        )

    def matches_route(self, route_metadata: OrderRouteMetadata) -> bool:
        """Return whether command route identity matches the submitted order route."""
        return self == route_metadata


__all__ = ["OrderRouteMetadata"]
