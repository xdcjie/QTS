"""Deprecated runtime session imports."""

from __future__ import annotations

import warnings

from qts.runtime.safety import RuntimeKillSwitchEvidence
from qts.runtime.session import RuntimeRollbackCommand, RuntimeRollbackEvidence
from qts.runtime.session import RuntimeSession as LiveRuntimeSession
from qts.runtime.session import RuntimeSessionResult as LiveRuntimeSessionResult

warnings.warn(
    "qts.runtime.live_runtime_session is deprecated; use qts.runtime.session.",
    DeprecationWarning,
    stacklevel=2,
)

LiveKillSwitchEvidence = RuntimeKillSwitchEvidence

__all__ = [
    "LiveKillSwitchEvidence",
    "LiveRuntimeSession",
    "LiveRuntimeSessionResult",
    "RuntimeRollbackCommand",
    "RuntimeRollbackEvidence",
]
