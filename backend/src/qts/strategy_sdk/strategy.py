"""User-facing Strategy base class."""

from __future__ import annotations


class Strategy:
    """Base class for user strategies."""

    def initialize(self, ctx: object) -> None:
        return None

    def on_bar(self, ctx: object, bar: object) -> None:
        return None

    def on_tick(self, ctx: object, tick: object) -> None:
        return None

    def on_timer(self, ctx: object, timer: object) -> None:
        return None

    def on_order_update(self, ctx: object, update: object) -> None:
        return None

    def on_fill(self, ctx: object, fill: object) -> None:
        return None

    def finalize(self, ctx: object) -> None:
        return None


__all__ = ["Strategy"]
