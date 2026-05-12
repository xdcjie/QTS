"""Small in-memory metrics registry for live-beta instrumentation."""

from __future__ import annotations

from collections.abc import Mapping

from qts.runtime.mailbox import Mailbox


class MetricsRegistry:
    """Record counters and gauges with deterministic key formatting."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._values: dict[str, int | float] = {}

    def increment(
        self,
        name: str,
        *,
        amount: int = 1,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        """Perform increment."""
        key = self._metric_key(name, tags)
        self._values[key] = int(self._values.get(key, 0)) + amount

    def gauge(
        self, name: str, value: int | float, *, tags: Mapping[str, str] | None = None
    ) -> None:
        """Perform gauge."""
        self._values[self._metric_key(name, tags)] = value

    def observe_queue(
        self,
        name: str,
        mailbox: Mailbox,
        *,
        oldest_message_lag_seconds: float,
    ) -> None:
        """Perform observe_queue."""
        self.gauge("queue.depth", mailbox.size, tags={"name": name})
        self.gauge(
            "queue.oldest_lag_seconds",
            oldest_message_lag_seconds,
            tags={"name": name},
        )

    def snapshot(self) -> dict[str, int | float]:
        """Perform snapshot."""
        return dict(sorted(self._values.items()))

    @staticmethod
    def _metric_key(name: str, tags: Mapping[str, str] | None) -> str:
        """Perform _metric_key."""
        if not name.strip():
            raise ValueError("metric name must not be empty")
        if not tags:
            return name
        tag_text = ",".join(f"{key}={tags[key]}" for key in sorted(tags))
        return f"{name}{{{tag_text}}}"


__all__ = ["MetricsRegistry"]
