"""Shared deterministic strategy for backtest/paper parity anchors.

The same intent must be emitted by both runtimes, so the strategy is owned in
one place and instantiated fresh per runtime (strategies hold per-run state).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from qts.strategy_sdk import Strategy


class ParityTargetQuantityStrategy(Strategy):
    """Emit one deterministic ``target_quantity`` on the first bar only.

    ``symbol`` and ``quantity`` are constructor inputs so a single helper drives
    both the backtest actor loop and the paper ``RuntimeSession`` with an
    identical intent.
    """

    def __init__(self, *, symbol: str = "AAPL", quantity: Decimal = Decimal("2")) -> None:
        """Configure the symbol and signed target quantity to request."""
        self._symbol = symbol
        self._quantity = quantity

    def initialize(self, ctx: Any) -> None:
        """Resolve the asset and reset the once-only guard."""
        self.asset = ctx.symbol(self._symbol)
        self._placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        """Request the target quantity exactly once, on the first bar."""
        del bar
        if not self._placed:
            ctx.target_quantity(self.asset, self._quantity)
            self._placed = True
