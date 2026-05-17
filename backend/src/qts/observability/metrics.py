"""Small in-memory metrics registry for runtime instrumentation."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import TYPE_CHECKING

from qts.runtime.mailbox import Mailbox

if TYPE_CHECKING:
    from qts.runtime.sinks.base import RuntimeEvent


class RuntimeCounterMetric(StrEnum):
    """Standard runtime counter metrics emitted across execution modes."""

    MARKET_DATA_EVENTS_TOTAL = "market_data_events_total"
    MARKET_DATA_STALE_TOTAL = "market_data_stale_total"
    MARKET_DATA_SUBSCRIPTION_FAILURES_TOTAL = "market_data_subscription_failures_total"
    STRATEGY_INTENTS_TOTAL = "strategy_intents_total"
    SIGNAL_CONFLICTS_TOTAL = "signal_conflicts_total"
    RISK_REJECTIONS_TOTAL = "risk_rejections_total"
    ORDERS_SUBMITTED_TOTAL = "orders_submitted_total"
    BROKER_REJECTIONS_TOTAL = "broker_rejections_total"
    FILLS_TOTAL = "fills_total"
    RECONCILIATION_DRIFTS_TOTAL = "reconciliation_drifts_total"
    KILL_SWITCH_ACTIVATIONS_TOTAL = "kill_switch_activations_total"
    RUNTIME_RECOVERY_BLOCKS_TOTAL = "runtime_recovery_blocks_total"


class RuntimeLatencyMetric(StrEnum):
    """Standard runtime latency metrics emitted across execution modes."""

    MARKET_DATA_INGEST_LATENCY = "market_data_ingest_latency"
    STRATEGY_EVAL_LATENCY = "strategy_eval_latency"
    SIGNAL_AGGREGATION_LATENCY = "signal_aggregation_latency"
    RISK_EVAL_LATENCY = "risk_eval_latency"
    ORDER_MANAGER_LATENCY = "order_manager_latency"
    BROKER_SUBMIT_LATENCY = "broker_submit_latency"
    BROKER_ACK_LATENCY = "broker_ack_latency"
    FILL_TO_ACCOUNT_APPLY_LATENCY = "fill_to_account_apply_latency"


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

    def record_latency(
        self,
        name: RuntimeLatencyMetric | str,
        seconds: int | float,
        *,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        """Record a runtime latency observation in seconds."""
        if seconds < 0:
            raise ValueError("latency seconds must be non-negative")
        self.gauge(str(name), seconds, tags=tags)

    def record_runtime_event(self, event: RuntimeEvent) -> None:
        """Increment standard metrics for normalized runtime events."""
        kind = event.kind.lower()
        if kind.startswith("market_data.") or kind == "runtime.market_data":
            self.increment(RuntimeCounterMetric.MARKET_DATA_EVENTS_TOTAL)
        if kind in {"risk.rejected", "runtime.risk_rejected"}:
            self.increment(
                RuntimeCounterMetric.RISK_REJECTIONS_TOTAL,
                tags=self._reason_code_tags(event.payload),
            )
        elif kind in {"market_data.stale", "runtime.market_data_stale"}:
            self.increment(RuntimeCounterMetric.MARKET_DATA_STALE_TOTAL)
        elif kind == "market_data_subscription_failed":
            self.increment(
                RuntimeCounterMetric.MARKET_DATA_SUBSCRIPTION_FAILURES_TOTAL,
                tags=self._reason_code_tags(event.payload),
            )
        elif kind in {"runtime.order_submitted", "execution.order.submitted"}:
            self.increment(RuntimeCounterMetric.ORDERS_SUBMITTED_TOTAL)
        elif kind in {"broker.order_rejected", "execution.broker_rejected"}:
            self.increment(
                RuntimeCounterMetric.BROKER_REJECTIONS_TOTAL,
                tags=self._reason_code_tags(event.payload),
            )
        elif kind in {"execution.fill.accepted", "runtime.fill_applied"}:
            self.increment(RuntimeCounterMetric.FILLS_TOTAL)
        elif kind in {"runtime.reconciliation_drift", "reconciliation.drift"}:
            self.increment(RuntimeCounterMetric.RECONCILIATION_DRIFTS_TOTAL)
        elif kind == "runtime.recovery_blocked":
            self.increment(
                RuntimeCounterMetric.RUNTIME_RECOVERY_BLOCKS_TOTAL,
                tags=self._reason_code_tags(event.payload),
            )
        elif kind == "risk.kill_switch_activated":
            self.increment(RuntimeCounterMetric.KILL_SWITCH_ACTIVATIONS_TOTAL)

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
    def _metric_key(
        name: RuntimeCounterMetric | RuntimeLatencyMetric | str, tags: Mapping[str, str] | None
    ) -> str:
        """Perform _metric_key."""
        metric_name = str(name)
        if not metric_name.strip():
            raise ValueError("metric name must not be empty")
        if not tags:
            return metric_name
        tag_text = ",".join(f"{key}={tags[key]}" for key in sorted(tags))
        return f"{metric_name}{{{tag_text}}}"

    @staticmethod
    def _reason_code_tags(payload: Mapping[str, object]) -> dict[str, str] | None:
        """Return metric tags for standard runtime reason codes."""
        reason_code = payload.get("reason_code")
        if reason_code is None:
            return None
        return {"reason_code": str(reason_code)}


__all__ = ["MetricsRegistry", "RuntimeCounterMetric", "RuntimeLatencyMetric"]
