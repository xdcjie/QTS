"""Route strategy-emitted order-lifecycle commands through OrderManagerActor.

Strategy code emits :class:`~qts.domain.orders.CancelIntent` via
``ctx.cancel_order(...)``; this module turns each cancel intent into a
:class:`~qts.runtime.actors.order_manager_actor.CancelOrder` actor message
using the route metadata the OrderManagerActor captured at submit time. The
SDK therefore never constructs broker route metadata itself (CLAUDE.md §8);
the runtime reconstructs it from the owning actor.
"""

from __future__ import annotations

from collections.abc import Iterable

from qts.core.ids import OrderId
from qts.domain.orders import CancelIntent
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.order_manager_actor import CancelOrder, GetRouteMetadata
from qts.runtime.order_route_metadata import OrderRouteMetadata


class CancelIntentRouter:
    """Route strategy cancel intents to an OrderManagerActor."""

    def __init__(
        self,
        *,
        order_manager_ref: ActorRef,
        execution_ref: ActorRef | None = None,
    ) -> None:
        """Create a router bound to one account's order manager.

        When ``execution_ref`` is supplied the router drives the full cancel
        round-trip (order manager -> execution adapter -> cancellation report ->
        order manager) so the order reaches its terminal cancelled state within
        the same step, mirroring how order submission is processed.
        """
        self._order_manager_ref = order_manager_ref
        self._execution_ref = execution_ref

    def route(self, cancel_intents: Iterable[CancelIntent]) -> tuple[OrderId, ...]:
        """Route cancel intents to CancelOrder; return routed order ids.

        The captured route metadata is authoritative for the order's account,
        strategy, and route, so the cancel reuses it directly and the
        OrderManagerActor's route match succeeds. Cancel intents whose order id
        is unknown to the order manager (no captured route metadata) are
        skipped: a strategy may reference an order that was never submitted or
        has already been compacted, and a cancel is fire-and-forget at the
        strategy level.
        """
        routed: list[OrderId] = []
        for intent in cancel_intents:
            route_metadata = self._route_metadata_for(intent.order_id)
            if route_metadata is None:
                continue
            self._order_manager_ref.tell(
                CancelOrder(
                    intent=intent,
                    account_id=route_metadata.account_id,
                    strategy_id=route_metadata.strategy_id,
                    route_metadata=route_metadata,
                )
            )
            routed.append(intent.order_id)
        if routed:
            self._order_manager_ref.process_all()
            if self._execution_ref is not None:
                self._execution_ref.process_all()
                self._order_manager_ref.process_all()
        return tuple(routed)

    def _route_metadata_for(self, order_id: OrderId) -> OrderRouteMetadata | None:
        try:
            return self._order_manager_ref.ask(GetRouteMetadata(order_id=order_id))
        except KeyError:
            return None


__all__ = ["CancelIntentRouter"]
