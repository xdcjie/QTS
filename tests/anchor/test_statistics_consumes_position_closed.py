"""Anchor: StatisticsBuilder trade metrics flow from PositionClosed events.

Domain fact: realized PnL per trade is computed by ``HoldingBook`` exactly
once and surfaced as an ``account.position_closed`` event. Downstream
consumers (statistics, reports) read the event, never re-derive PnL from
fills.

Owner: ``StatisticsBuilder.on_position_close``.

Forbidden shortcut: keeping ``_OpenTrade`` as a parallel trade aggregator
in the builder.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.reporting.statistics import StatisticsBuilder


def test_position_close_events_drive_trade_level_metrics() -> None:
    builder = StatisticsBuilder()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    for index, equity in enumerate(
        (
            Decimal("100000"),
            Decimal("100050"),
            Decimal("100100"),
            Decimal("100075"),
            Decimal("100200"),
        )
    ):
        builder.on_equity_point(time=start + timedelta(minutes=index), equity=equity)

    # Three closed trades fed in directly through the position-closed path.
    builder.on_position_close(realized_pnl=Decimal("50"), holding_bars=1)
    builder.on_position_close(realized_pnl=Decimal("-25"), holding_bars=2)
    builder.on_position_close(realized_pnl=Decimal("125"), holding_bars=1)

    payload = builder.finalize(trading_bars=4, bars_per_year=Decimal("252")).to_payload()

    assert payload["total_trades"] == 3
    assert payload["win_rate"] == Decimal("2") / Decimal("3")
    assert payload["loss_rate"] == Decimal("1") / Decimal("3")
    # avg_win = (50 + 125) / 2; avg_loss = -25
    assert payload["avg_win"] == Decimal("87.5")
    assert payload["avg_loss"] == Decimal("-25")
    assert payload["largest_win"] == Decimal("125")
    assert payload["largest_loss"] == Decimal("-25")
    # profit_factor = (50 + 125) / 25 = 7
    assert payload["profit_factor"] == Decimal("7")
    # expectancy = mean of [50, -25, 125] = 50
    assert payload["expectancy"] == Decimal("50")
    # avg_holding_period_bars = (1 + 2 + 1) / 3
    assert payload["avg_holding_period_bars"] == (
        Decimal("1") + Decimal("2") + Decimal("1")
    ) / Decimal("3")


def test_on_fill_records_cost_metrics_without_creating_trades() -> None:
    """on_fill is the cost path only; trades come from on_position_close."""
    builder = StatisticsBuilder()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    builder.on_equity_point(time=start, equity=Decimal("100000"))
    builder.on_equity_point(time=start + timedelta(minutes=1), equity=Decimal("100050"))

    builder.on_fill(
        order_id="ord-1",
        instrument_id="EQUITY.US.NASDAQ.AAPL",
        side="buy",
        quantity=Decimal("10"),
        price=Decimal("100"),
        commission=Decimal("1"),
        slippage=Decimal("0.5"),
        fill_time=start,
    )

    payload = builder.finalize(trading_bars=1, bars_per_year=Decimal("252")).to_payload()

    # Cost metrics recorded
    assert payload["total_orders"] == 1
    assert payload["total_commission"] == Decimal("1")
    assert payload["total_slippage"] == Decimal("0.5")
    # But no trade was closed → trade-level fields are zero
    assert payload["total_trades"] == 0
    assert payload["win_rate"] == Decimal("0")
    assert payload["expectancy"] == Decimal("0")


def test_open_trade_dataclass_is_removed_from_builder() -> None:
    """Guardrail-style: the deprecated parallel tracker no longer exists."""
    import qts.reporting.statistics as stats_module

    assert not hasattr(stats_module, "_OpenTrade")
