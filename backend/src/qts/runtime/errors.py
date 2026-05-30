"""Runtime-orchestration exception taxonomy.

These distinguish operator/control-plane and safety failures: a command issued
with no runtime bound, a command rejected by the runtime, and a violated
safety invariant.
"""

from __future__ import annotations

from qts.core.errors import QTSRuntimeError


class RuntimeCommandNotBound(QTSRuntimeError):
    """An operator command was issued but no RuntimeSession is bound to handle it."""


class RuntimeCommandRejected(QTSRuntimeError):
    """An operator command reached the runtime but was rejected."""


class RuntimeSafetyViolation(QTSRuntimeError):
    """A safety-critical runtime invariant was violated."""


__all__ = [
    "RuntimeCommandNotBound",
    "RuntimeCommandRejected",
    "RuntimeSafetyViolation",
]
