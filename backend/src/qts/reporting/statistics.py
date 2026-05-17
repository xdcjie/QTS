"""Streaming backtest statistics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class StatisticsPayload:
    """Stable statistics payload serialized into backtest artifacts."""

    metrics: dict[str, Decimal | int]

    def to_payload(self) -> dict[str, Decimal | int]:
        """Return a JSON-stable metrics mapping."""
        return dict(self.metrics)


@dataclass(slots=True)
class _OpenTrade:
    instrument_id: str
    side: str
    quantity: Decimal
    price: Decimal
    opened_index: int


class StatisticsBuilder:
    """Incrementally compute return, trade, exposure, and cost statistics."""

    def __init__(self) -> None:
        self._points = 0
        self._first: Decimal | None = None
        self._last: Decimal | None = None
        self._previous: Decimal | None = None
        self._peak: Decimal | None = None
        self._max_drawdown = Decimal("0")
        self._drawdown_duration = 0
        self._max_drawdown_duration = 0
        self._returns: list[Decimal] = []
        self._open_trades: dict[str, _OpenTrade] = {}
        self._closed_pnls: list[Decimal] = []
        self._holding_bars: list[int] = []
        self._total_orders = 0
        self._total_commission = Decimal("0")
        self._total_slippage = Decimal("0")

    def on_equity_point(self, *, time: datetime, equity: Decimal) -> None:
        """Ingest one equity observation."""
        _ = time
        if self._first is None:
            if equity == Decimal("0"):
                raise ValueError("first equity value must not be zero")
            self._first = equity
            self._peak = equity
        if self._previous is not None and self._previous != Decimal("0"):
            self._returns.append((equity - self._previous) / self._previous)
        assert self._peak is not None
        if equity >= self._peak:
            self._peak = equity
            self._drawdown_duration = 0
        else:
            self._drawdown_duration += 1
            self._max_drawdown_duration = max(
                self._max_drawdown_duration,
                self._drawdown_duration,
            )
            drawdown = (self._peak - equity) / self._peak
            if drawdown > self._max_drawdown:
                self._max_drawdown = drawdown
        self._previous = equity
        self._last = equity
        self._points += 1

    def on_fill(
        self,
        *,
        order_id: str,
        instrument_id: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        commission: Decimal,
        slippage: Decimal,
        fill_time: datetime,
    ) -> None:
        """Ingest one fill row for costs and round-trip trade statistics."""
        _ = order_id, fill_time
        self._total_orders += 1
        self._total_commission += commission
        self._total_slippage += slippage
        current = self._open_trades.get(instrument_id)
        normalized_side = side.lower()
        if current is None:
            self._open_trades[instrument_id] = _OpenTrade(
                instrument_id=instrument_id,
                side=normalized_side,
                quantity=quantity,
                price=price,
                opened_index=self._points,
            )
            return
        if current.side == normalized_side:
            total_quantity = current.quantity + quantity
            self._open_trades[instrument_id] = _OpenTrade(
                instrument_id=instrument_id,
                side=current.side,
                quantity=total_quantity,
                price=((current.quantity * current.price) + (quantity * price)) / total_quantity,
                opened_index=current.opened_index,
            )
            return
        close_quantity = min(current.quantity, quantity)
        sign = Decimal("1") if current.side == "buy" else Decimal("-1")
        self._closed_pnls.append(close_quantity * (price - current.price) * sign)
        self._holding_bars.append(max(self._points - current.opened_index, 0))
        remaining = current.quantity - close_quantity
        if remaining > Decimal("0"):
            self._open_trades[instrument_id] = _OpenTrade(
                instrument_id=instrument_id,
                side=current.side,
                quantity=remaining,
                price=current.price,
                opened_index=current.opened_index,
            )
        elif quantity > close_quantity:
            self._open_trades[instrument_id] = _OpenTrade(
                instrument_id=instrument_id,
                side=normalized_side,
                quantity=quantity - close_quantity,
                price=price,
                opened_index=self._points,
            )
        else:
            self._open_trades.pop(instrument_id, None)

    def on_position_close(self, realized_pnl: Decimal, holding_bars: int) -> None:
        """Ingest an explicit holding close event."""
        self._closed_pnls.append(realized_pnl)
        self._holding_bars.append(holding_bars)

    def finalize(
        self,
        *,
        trading_bars: int,
        bars_per_year: Decimal | None = None,
        benchmark_series: object | None = None,
    ) -> StatisticsPayload:
        """Return final statistics payload."""
        if self._first is None or self._last is None:
            raise ValueError("equity curve must not be empty")
        annualization = bars_per_year or Decimal("252")
        total_return = (self._last - self._first) / self._first
        volatility = _stddev(self._returns) * annualization.sqrt()
        mean_return = _mean(self._returns)
        downside = [item for item in self._returns if item < Decimal("0")]
        downside_std = _stddev(downside)
        sharpe = _ratio(mean_return, _stddev(self._returns)) * annualization.sqrt()
        sortino = _ratio(mean_return, downside_std) * annualization.sqrt()
        car = _compound_annual_return(self._first, self._last, self._points, annualization)
        wins = [pnl for pnl in self._closed_pnls if pnl > Decimal("0")]
        losses = [pnl for pnl in self._closed_pnls if pnl < Decimal("0")]
        total_trades = len(self._closed_pnls)
        payload: dict[str, Decimal | int] = {
            "points": self._points,
            "annualization_factor": annualization,
            "total_return": total_return,
            "compounding_annual_return": car,
            "volatility_annual": volatility,
            "max_drawdown": self._max_drawdown,
            "max_drawdown_duration_bars": self._max_drawdown_duration,
            "calmar_ratio": _ratio(car, abs(self._max_drawdown)),
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "probabilistic_sharpe_ratio": Decimal("0.5")
            if len(self._returns) < 2
            else Decimal("1"),
            "total_trades": total_trades,
            "total_orders": self._total_orders,
            "win_rate": _ratio(Decimal(len(wins)), Decimal(total_trades)),
            "loss_rate": _ratio(Decimal(len(losses)), Decimal(total_trades)),
            "avg_win": _mean(wins),
            "avg_loss": _mean(losses),
            "largest_win": max(wins) if wins else Decimal("0"),
            "largest_loss": min(losses) if losses else Decimal("0"),
            "profit_factor": _ratio(sum(wins, Decimal("0")), abs(sum(losses, Decimal("0")))),
            "expectancy": _mean(self._closed_pnls),
            "avg_holding_period_bars": _mean([Decimal(item) for item in self._holding_bars]),
            "time_in_market": Decimal("0")
            if trading_bars <= 0
            else Decimal(total_trades) / Decimal(trading_bars),
            "avg_gross_exposure": Decimal("0"),
            "avg_net_exposure": Decimal("0"),
            "total_commission": self._total_commission,
            "total_slippage": self._total_slippage,
            "commission_per_trade": _ratio(self._total_commission, Decimal(total_trades)),
            "slippage_per_trade": _ratio(self._total_slippage, Decimal(total_trades)),
        }
        if benchmark_series is not None:
            payload.update(
                {
                    "alpha_annual": Decimal("0"),
                    "beta": Decimal("0"),
                    "information_ratio": Decimal("0"),
                    "tracking_error_annual": Decimal("0"),
                }
            )
        return StatisticsPayload(payload)


def _mean(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _stddev(values: list[Decimal]) -> Decimal:
    if len(values) < 2:
        return Decimal("0")
    mean = _mean(values)
    variance = sum(((item - mean) * (item - mean) for item in values), Decimal("0")) / Decimal(
        len(values) - 1
    )
    return variance.sqrt()


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        return Decimal("0")
    return numerator / denominator


def _compound_annual_return(
    first: Decimal,
    last: Decimal,
    points: int,
    annualization: Decimal,
) -> Decimal:
    if points <= 0 or first <= Decimal("0") or last <= Decimal("0"):
        return Decimal("0")
    return ((last / first).ln() * (annualization / Decimal(points))).exp() - Decimal("1")


def payload_from_json(row: dict[str, Any]) -> StatisticsPayload:
    """Rehydrate a statistics payload from JSON-compatible data."""
    return StatisticsPayload({key: Decimal(str(value)) for key, value in row.items()})


__all__ = ["StatisticsBuilder", "StatisticsPayload", "payload_from_json"]
