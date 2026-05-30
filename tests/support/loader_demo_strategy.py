"""Minimal Strategy used to exercise StrategyLoader in unit tests.

Lives in the stable ``tests.support`` package (imported by its full dotted
name) so ``StrategyLoader``'s ``importlib`` load returns the same module object
the test imports, keeping ``isinstance`` checks meaningful.
"""

from __future__ import annotations

from typing import Any

from qts.strategy_sdk import Strategy


class DemoStrategy(Strategy):
    """No-op strategy that records the params it was constructed with."""

    def __init__(self, **params: Any) -> None:
        self.params = params

    def initialize(self, ctx: Any) -> None:
        """No-op initialize."""

    def on_bar(self, ctx: Any, bar: object) -> None:
        """No-op bar handler."""
