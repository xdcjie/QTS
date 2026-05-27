"""Streaming backtest statistics.

Owns the math for return / risk-adjusted / trade-level / exposure statistics
emitted by ``BacktestArtifactWriter``. Every metric is either computed from
real data or omitted; no field is filled with a sentinel constant.

PSR uses the López de Prado formulation (``ProbabilisticSharpeRatio``). The
normal CDF step is evaluated in ``float`` (sufficient precision for a
probability) while every other accumulator stays ``Decimal`` for parity with
the rest of the reporting stack.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class StatisticsPayload:
    """Stable statistics payload serialized into backtest artifacts."""

    metrics: dict[str, Decimal | int]

    def to_payload(self) -> dict[str, Decimal | int]:
        """Return a JSON-stable metrics mapping."""
        return dict(self.metrics)


@dataclass(frozen=True, slots=True)
class _HoldingsSnapshot:
    """One per-bar holdings snapshot used for exposure averaging."""

    gross_notional: Decimal
    net_notional: Decimal


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
        self._equity_points: list[Decimal] = []
        self._open_instruments: set[str] = set()
        self._closed_pnls: list[Decimal] = []
        self._holding_bars: list[int] = []
        self._total_orders = 0
        self._total_commission = Decimal("0")
        self._total_slippage = Decimal("0")
        self._occupied_bars = 0
        self._holdings_snapshots: list[_HoldingsSnapshot] = []
        self._dates_seen: set[date] = set()

    def on_equity_point(self, *, time: datetime, equity: Decimal) -> None:
        """Ingest one equity observation."""
        self._dates_seen.add(time.date())
        if self._first is None:
            if equity == Decimal("0"):
                raise ValueError("first equity value must not be zero")
            self._first = equity
            self._peak = equity
        if self._previous is not None and self._previous != Decimal("0"):
            self._returns.append((equity - self._previous) / self._previous)
        if self._open_instruments:
            self._occupied_bars += 1
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
        self._equity_points.append(equity)

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
        """Ingest one fill row.

        Records cost (commission, slippage, total_orders) and marks the
        instrument as held for the ``time_in_market`` exposure counter.
        Trade-level realized PnL is **not** computed here — it flows through
        ``on_position_close`` from ``account.position_closed`` events so
        Holdings stays the single source of truth.
        """
        _ = order_id, side, quantity, price, fill_time
        self._total_orders += 1
        self._total_commission += commission
        self._total_slippage += slippage
        self._open_instruments.add(instrument_id)

    def on_position_close(
        self,
        realized_pnl: Decimal,
        holding_bars: int,
        instrument_id: str | None = None,
    ) -> None:
        """Ingest one holding close event.

        Appends realized PnL and holding period to the trade-level lists used
        by the finalize step. When ``instrument_id`` is supplied, clears the
        open-instrument tracker so ``time_in_market`` stops counting that
        instrument as held.
        """
        self._closed_pnls.append(realized_pnl)
        self._holding_bars.append(holding_bars)
        if instrument_id is not None:
            self._open_instruments.discard(instrument_id)

    def on_holdings_snapshot(
        self,
        *,
        gross_notional: Decimal,
        net_notional: Decimal,
    ) -> None:
        """Ingest one per-bar holdings snapshot for exposure averaging.

        Exposure fields ``avg_gross_exposure`` and ``avg_net_exposure`` appear
        in the finalized payload only when the caller has fed at least one
        snapshot through this method.
        """
        if gross_notional < Decimal("0"):
            raise ValueError("gross_notional must be non-negative")
        self._holdings_snapshots.append(
            _HoldingsSnapshot(gross_notional=gross_notional, net_notional=net_notional)
        )

    def finalize(
        self,
        *,
        trading_bars: int,
        bars_per_year: Decimal | None = None,
        benchmark_returns: tuple[Decimal, ...] | None = None,
    ) -> StatisticsPayload:
        """Return final statistics payload.

        ``benchmark_returns`` must be aligned bar-for-bar with the strategy's
        per-period return series (i.e. one element per equity point after the
        first).
        """
        if self._first is None or self._last is None:
            raise ValueError("equity curve must not be empty")
        annualization = bars_per_year or self._derive_annualization()
        total_return = (self._last - self._first) / self._first
        std = _stddev(self._returns)
        volatility = std * annualization.sqrt()
        mean_return = _mean(self._returns)
        downside = [item for item in self._returns if item < Decimal("0")]
        downside_std = _stddev(downside)
        sharpe = _ratio(mean_return, std) * annualization.sqrt()
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
            "probabilistic_sharpe_ratio": _probabilistic_sharpe_ratio(self._returns),
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
            "time_in_market": _ratio(
                Decimal(self._occupied_bars),
                Decimal(max(trading_bars, 0)),
            ),
            "total_commission": self._total_commission,
            "total_slippage": self._total_slippage,
            "commission_per_trade": _ratio(self._total_commission, Decimal(total_trades)),
            "slippage_per_trade": _ratio(self._total_slippage, Decimal(total_trades)),
        }
        bench = self._benchmark_returns_or_none(benchmark_returns)
        if bench is not None:
            payload.update(_benchmark_metrics(self._returns, bench, annualization))
        if self._holdings_snapshots:
            payload.update(self._exposure_metrics())
        return StatisticsPayload(payload)

    def _benchmark_returns_or_none(
        self,
        benchmark_returns: tuple[Decimal, ...] | None,
    ) -> tuple[Decimal, ...] | None:
        if benchmark_returns is not None:
            return benchmark_returns
        return None

    def _derive_annualization(self) -> Decimal:
        """Return the default annualization factor when none is given.

        Computed as ``252 × bars_per_day`` where ``bars_per_day`` is the
        ratio of observed equity points to distinct calendar dates in
        the equity curve. Falls back to ``252`` when only one day was
        observed (or fewer points than days, which shouldn't happen).
        """
        observed_days = max(len(self._dates_seen), 1)
        if self._points <= 0:
            return Decimal("252")
        bars_per_day = Decimal(self._points) / Decimal(observed_days)
        return Decimal("252") * bars_per_day

    def _exposure_metrics(self) -> dict[str, Decimal]:
        # Align snapshot i to equity point i; compute fraction of equity.
        snapshots = self._holdings_snapshots
        equity = self._equity_points
        pairs = min(len(snapshots), len(equity))
        if pairs == 0:
            return {}
        gross_fractions: list[Decimal] = []
        net_fractions: list[Decimal] = []
        for index in range(pairs):
            denom = equity[index]
            if denom == Decimal("0"):
                gross_fractions.append(Decimal("0"))
                net_fractions.append(Decimal("0"))
                continue
            gross_fractions.append(snapshots[index].gross_notional / denom)
            net_fractions.append(snapshots[index].net_notional / denom)
        return {
            "avg_gross_exposure": _mean(gross_fractions),
            "avg_net_exposure": _mean(net_fractions),
        }


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


def _probabilistic_sharpe_ratio(returns: list[Decimal]) -> Decimal:
    """Compute López de Prado's Probabilistic Sharpe Ratio with SR_benchmark = 0.

    PSR = Φ( SR̂ · √(n-1) / √(1 - skew · SR̂ + (kurt-1)/4 · SR̂²) ).
    """
    if len(returns) < 4:
        return Decimal("0")
    sample = [float(r) for r in returns]
    n = len(sample)
    mean = sum(sample) / n
    variance = sum((r - mean) ** 2 for r in sample) / (n - 1)
    if variance <= 0.0:
        return Decimal("0")
    std = math.sqrt(variance)
    sharpe = mean / std
    skew = sum(((r - mean) / std) ** 3 for r in sample) / n
    kurt = sum(((r - mean) / std) ** 4 for r in sample) / n
    denom_squared = 1.0 - skew * sharpe + (kurt - 1.0) / 4.0 * sharpe**2
    if denom_squared <= 0.0:
        return Decimal("0")
    sigma_sharpe = math.sqrt(denom_squared / (n - 1))
    if sigma_sharpe == 0.0:
        return Decimal("0")
    z = sharpe / sigma_sharpe
    probability = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return Decimal(str(probability))


def _benchmark_metrics(
    returns: list[Decimal],
    bench: tuple[Decimal, ...],
    annualization: Decimal,
) -> dict[str, Decimal]:
    n = min(len(returns), len(bench))
    if n < 2:
        return {
            "alpha_annual": Decimal("0"),
            "beta": Decimal("0"),
            "information_ratio": Decimal("0"),
            "tracking_error_annual": Decimal("0"),
        }
    r_values = [returns[i] for i in range(n)]
    b_values = [bench[i] for i in range(n)]
    mean_r = _mean(r_values)
    mean_b = _mean(b_values)
    cov = sum(
        ((r_values[i] - mean_r) * (b_values[i] - mean_b) for i in range(n)),
        Decimal("0"),
    ) / Decimal(n - 1)
    var_b = sum(((b_values[i] - mean_b) ** 2 for i in range(n)), Decimal("0")) / Decimal(n - 1)
    if var_b == Decimal("0"):
        beta = Decimal("0")
    else:
        beta = cov / var_b
    alpha_period = mean_r - beta * mean_b
    diffs = [r_values[i] - b_values[i] for i in range(n)]
    mean_diff = _mean(diffs)
    diff_std = _stddev(diffs)
    sqrt_annualization = annualization.sqrt()
    if diff_std == Decimal("0"):
        information_ratio = Decimal("0")
    else:
        information_ratio = (mean_diff / diff_std) * sqrt_annualization
    return {
        "alpha_annual": alpha_period * annualization,
        "beta": beta,
        "tracking_error_annual": diff_std * sqrt_annualization,
        "information_ratio": information_ratio,
    }


def payload_from_json(row: dict[str, Any]) -> StatisticsPayload:
    """Rehydrate a statistics payload from JSON-compatible data."""
    return StatisticsPayload({key: Decimal(str(value)) for key, value in row.items()})


__all__ = ["StatisticsBuilder", "StatisticsPayload", "payload_from_json"]
