"""Shared runtime event writers for risk/order/fill observability."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from qts.core.ids import AccountId, CausationId, CorrelationId, InstrumentId, StrategyId
from qts.domain.orders import Order, OrderFill
from qts.domain.risk import RiskDecision
from qts.portfolio.holdings import PositionClosed
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.order_manager_actor import GetOrder, GetRouteMetadata
from qts.runtime.order_route_metadata import OrderRouteMetadata
from qts.runtime.sinks.base import RuntimeEvent


@dataclass(frozen=True, slots=True)
class RuntimeEventWriter:
    """Write runtime observability events for order flow and risk decisions."""

    write: Callable[[RuntimeEvent], object | None]

    def write_risk_decision_events(
        self,
        risk_decisions: tuple[RiskDecision, ...],
        *,
        correlation_id: CorrelationId,
        account_id: AccountId | None,
        instrument_id: InstrumentId,
        strategy_id: StrategyId,
    ) -> None:
        """Write approved/rejected risk decision events."""
        for decision in risk_decisions:
            self.write(
                RuntimeEvent(
                    kind="runtime.risk_decision",
                    payload=self._risk_decision_payload(decision),
                    correlation_id=correlation_id,
                    account_id=account_id,
                    instrument_id=instrument_id,
                    strategy_id=strategy_id,
                )
            )
            if not decision.approved:
                self.write(
                    RuntimeEvent(
                        kind="runtime.risk_rejected",
                        payload=self._risk_decision_payload(decision),
                        correlation_id=correlation_id,
                        account_id=account_id,
                        instrument_id=instrument_id,
                        strategy_id=strategy_id,
                    )
                )

    def write_order_events(
        self,
        orders: tuple[Order, ...],
        order_manager_ref: ActorRef,
        *,
        fallback_contributing_strategy_ids: tuple[StrategyId, ...] = (),
    ) -> None:
        """Write submitted/order-state events for emitted orders."""
        for order in orders:
            metadata: OrderRouteMetadata = order_manager_ref.ask(
                GetRouteMetadata(order_id=order.order_id)
            )
            contributing_strategy_ids = (
                metadata.contributing_strategy_ids or fallback_contributing_strategy_ids
            )
            self.write(
                RuntimeEvent(
                    kind="runtime.order_submitted",
                    payload={
                        "order_id": order.order_id.value,
                        "broker_order_id": order.broker_order_id,
                        "client_order_id": metadata.client_order_id,
                        "instrument_id": order.intent.instrument_id.value,
                        "order_spec": order.intent.order_spec.to_payload(),
                        "aggregation_decision_id": metadata.aggregation_decision_id,
                        "contributing_strategy_ids": [
                            strategy_id.value for strategy_id in contributing_strategy_ids
                        ],
                    },
                    correlation_id=metadata.correlation_id,
                    instrument_id=order.intent.instrument_id,
                    strategy_id=metadata.strategy_id,
                    account_id=metadata.account_id,
                )
            )
            self.write(
                RuntimeEvent(
                    kind="runtime.broker_report",
                    payload={
                        "order_id": order.order_id.value,
                        "state": order.state.value,
                        "order_spec": order.intent.order_spec.to_payload(),
                        "broker_order_id": order.broker_order_id,
                        "client_order_id": metadata.client_order_id,
                        "aggregation_decision_id": metadata.aggregation_decision_id,
                        "contributing_strategy_ids": [
                            strategy_id.value for strategy_id in contributing_strategy_ids
                        ],
                    },
                    correlation_id=metadata.correlation_id,
                    instrument_id=order.intent.instrument_id,
                    strategy_id=metadata.strategy_id,
                    account_id=metadata.account_id,
                    causation_id=CausationId(f"{metadata.client_order_id}:order_submitted"),
                )
            )

    def write_fill_events(
        self,
        fills: tuple[OrderFill, ...],
        order_manager_ref: ActorRef,
    ) -> None:
        """Write fill events with routing metadata and account context."""
        for fill in fills:
            metadata: OrderRouteMetadata = order_manager_ref.ask(
                GetRouteMetadata(order_id=fill.order_id)
            )
            order: Order = order_manager_ref.ask(GetOrder(order_id=fill.order_id))
            self.write(
                RuntimeEvent(
                    kind="runtime.fill_applied",
                    payload={
                        "fill_id": fill.fill_id,
                        "order_id": fill.order_id.value,
                        "broker_order_id": order.broker_order_id,
                        "client_order_id": metadata.client_order_id,
                        "instrument_id": fill.instrument_id.value,
                        "side": fill.side.value,
                        "quantity": str(fill.quantity),
                        "price": str(fill.price),
                        "commission": str(fill.commission),
                        "slippage": str(fill.slippage),
                    },
                    correlation_id=metadata.correlation_id,
                    instrument_id=fill.instrument_id,
                    strategy_id=metadata.strategy_id,
                    account_id=metadata.account_id,
                    causation_id=CausationId(f"{metadata.client_order_id}:broker_report"),
                )
            )

    def write_position_closed_events(
        self,
        events: tuple[PositionClosed, ...],
        *,
        account_id: AccountId | None,
        strategy_id: StrategyId | None = None,
        correlation_id: CorrelationId | None = None,
    ) -> None:
        """Write account.position_closed events into the runtime sink.

        These events are the single source of truth for trade-level realized
        PnL; the backtest artifact writer persists them into
        ``closed_trades.ndjson`` and the statistics builder consumes them in
        place of its previous private fill tracker.
        """
        for closed in events:
            self.write(
                RuntimeEvent(
                    kind="account.position_closed",
                    payload={
                        "instrument_id": closed.instrument_id.value,
                        "closed_quantity": str(closed.closed_quantity),
                        "exit_price": str(closed.exit_price),
                        "realized_pnl": str(closed.realized_pnl),
                        "opened_at": (
                            None if closed.opened_at is None else closed.opened_at.isoformat()
                        ),
                        "closed_at": closed.closed_at.isoformat(),
                    },
                    account_id=account_id,
                    strategy_id=strategy_id,
                    instrument_id=closed.instrument_id,
                    correlation_id=correlation_id,
                )
            )

    @staticmethod
    def _risk_decision_payload(decision: RiskDecision) -> dict[str, object]:
        """Serialize shared risk decision fields for runtime events."""
        payload: dict[str, object] = {
            "rule_id": decision.rule_id,
            "aggregation_decision_id": decision.aggregation_decision_id,
            "contributing_strategy_ids": [
                strategy_id.value for strategy_id in decision.contributing_strategy_ids
            ],
            "conflict_reason": decision.conflict_reason,
            "evidence": dict(decision.evidence),
        }
        if decision.approved:
            payload["approved"] = True
        else:
            payload.update(
                {
                    "approved": False,
                    "reason_code": decision.reason_code,
                    "reason": decision.reason,
                }
            )
        return payload


__all__ = ["RuntimeEventWriter"]
