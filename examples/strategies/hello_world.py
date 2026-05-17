"""Minimal hello-world strategy used in docs/GETTING_STARTED.md.

The strategy opens a single long position on the first bar and holds.
It is intentionally tiny: every line corresponds to one concept in
the Strategy SDK (``initialize``, ``ctx.symbol``, ``on_bar``,
``ctx.target_quantity``) so new users can read it top-to-bottom and
understand the full flow in under a minute.
"""

from __future__ import annotations

from decimal import Decimal

from qts.strategy_sdk import Strategy


class HelloWorldStrategy(Strategy):
    """Buy one share on the first bar and hold."""

    def initialize(self, ctx):  # type: ignore[no-untyped-def]
        self.asset = ctx.symbol("AAPL")
        self._opened = False

    def on_bar(self, ctx, bar):  # type: ignore[no-untyped-def]
        if self._opened:
            return
        ctx.target_quantity(self.asset, Decimal("1"))
        self._opened = True
