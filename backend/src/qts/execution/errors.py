"""Execution-domain exception taxonomy.

These distinguish the execution/order-lifecycle failure modes that operators and
runtime actors must react to differently: risk rejection, lifecycle/state
violations, unknown order/broker references, duplicate execution reports,
unsupported capabilities, and missing fill data.
"""

from __future__ import annotations

from qts.core.errors import QTSError, QTSInvariantError


class OrderLifecycleError(QTSInvariantError):
    """An order state-machine / lifecycle transition was attempted illegally."""


class RiskRejectedOrder(QTSError):
    """An order intent was rejected by the risk boundary and must not proceed."""


class UnknownOrder(QTSInvariantError):
    """A referenced internal order id is not tracked by the order manager."""


class UnknownBrokerOrder(QTSInvariantError):
    """A referenced broker order id is not mapped to any tracked order."""


class DuplicateExecutionReport(QTSInvariantError):
    """An execution report was already applied (idempotency violation)."""


class UnsupportedOrderReplace(QTSError):
    """Order replace was requested for a broker/order that does not support it."""


class MissingFillPrice(QTSInvariantError):
    """A fill report carried a filled quantity without a required fill price."""


__all__ = [
    "DuplicateExecutionReport",
    "MissingFillPrice",
    "OrderLifecycleError",
    "RiskRejectedOrder",
    "UnknownBrokerOrder",
    "UnknownOrder",
    "UnsupportedOrderReplace",
]
