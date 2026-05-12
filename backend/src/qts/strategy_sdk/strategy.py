"""User-facing Strategy base class."""

from __future__ import annotations


class Strategy:
    """Base class for user strategies."""

    def initialize(self, ctx: object) -> None:
        """Perform initialize."""
        return None

    def on_bar(self, ctx: object, bar: object) -> None:
        """Perform on_bar."""
        return None

    def on_tick(self, ctx: object, tick: object) -> None:
        """Perform on_tick."""
        return None

    def on_timer(self, ctx: object, timer: object) -> None:
        """Perform on_timer."""
        return None

    def on_order_update(self, ctx: object, update: object) -> None:
        """Perform on_order_update."""
        return None

    def on_fill(self, ctx: object, fill: object) -> None:
        """Perform on_fill."""
        return None

    def finalize(self, ctx: object) -> None:
        """Perform finalize."""
        return None


__all__ = ["Strategy"]
