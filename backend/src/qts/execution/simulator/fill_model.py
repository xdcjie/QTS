"""Deterministic simulated fill model."""

from __future__ import annotations

from decimal import Decimal

from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus, OrderIntent


class ImmediateFillModel:
    """Fills market orders at the provided market price."""

    def fill(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        """Perform fill."""
        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill-1",
        )


class NextBarOpenFillModel:
    """Fills orders at the next visible bar open price."""

    def fill(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        next_open_price: Decimal | None = None,
    ) -> ExecutionReport:
        """Fill at next_open_price when supplied, otherwise at market_price."""

        fill_price = market_price if next_open_price is None else next_open_price
        if fill_price < Decimal("0"):
            raise ValueError("fill price must be non-negative")
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=fill_price,
            fill_id=f"{broker_order_id}-fill-1",
        )


class QuoteAwareFillModel:
    """Fills buy orders at ask and sell orders at bid when quote data is present."""

    def fill(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        bid_price: Decimal | None = None,
        ask_price: Decimal | None = None,
    ) -> ExecutionReport:
        """Fill with quote-side pricing when bid/ask are available."""

        from qts.domain.orders import OrderSide

        if intent.side is OrderSide.BUY and ask_price is not None:
            fill_price = ask_price
        elif intent.side is OrderSide.SELL and bid_price is not None:
            fill_price = bid_price
        else:
            fill_price = market_price
        if fill_price < Decimal("0"):
            raise ValueError("fill price must be non-negative")
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=fill_price,
            fill_id=f"{broker_order_id}-fill-1",
        )


class VolumeParticipationFillModel:
    """Caps simulated fill quantity by visible volume participation."""

    def __init__(self, *, max_participation_rate: Decimal) -> None:
        self._max_participation_rate = Decimal(str(max_participation_rate))
        if self._max_participation_rate <= Decimal("0") or self._max_participation_rate > Decimal(
            "1"
        ):
            raise ValueError("max_participation_rate must be in (0, 1]")

    def fill(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        available_volume: Decimal | None = None,
    ) -> ExecutionReport:
        """Fill at most the configured share of visible volume."""

        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        fill_quantity = intent.quantity
        if available_volume is not None:
            if available_volume < Decimal("0"):
                raise ValueError("available_volume must be non-negative")
            fill_quantity = min(intent.quantity, available_volume * self._max_participation_rate)
        status = (
            ExecutionReportStatus.FILLED
            if fill_quantity == intent.quantity
            else ExecutionReportStatus.PARTIALLY_FILLED
        )
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=status,
            filled_quantity=fill_quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill-1",
        )


class PartialFillModel:
    """Caps simulated fill quantity at a deterministic maximum."""

    def __init__(self, *, max_fill_quantity: Decimal) -> None:
        self._max_fill_quantity = Decimal(str(max_fill_quantity))
        if self._max_fill_quantity <= Decimal("0"):
            raise ValueError("max_fill_quantity must be positive")

    def fill(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
    ) -> ExecutionReport:
        """Fill no more than max_fill_quantity."""

        if market_price < Decimal("0"):
            raise ValueError("market_price must be non-negative")
        fill_quantity = min(intent.quantity, self._max_fill_quantity)
        status = (
            ExecutionReportStatus.FILLED
            if fill_quantity == intent.quantity
            else ExecutionReportStatus.PARTIALLY_FILLED
        )
        return ExecutionReport(
            report_id=f"{broker_order_id}-report-1",
            broker_order_id=broker_order_id,
            status=status,
            filled_quantity=fill_quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill-1",
        )


__all__ = [
    "ImmediateFillModel",
    "NextBarOpenFillModel",
    "PartialFillModel",
    "QuoteAwareFillModel",
    "VolumeParticipationFillModel",
]
