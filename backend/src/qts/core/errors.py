"""Base domain exception taxonomy for the quant trading system.

Production code distinguishes business/operational failures from generic
built-in errors so callers and operators can react to the failure *kind*
(configuration, invariant violation, runtime orchestration) rather than parsing
``ValueError``/``KeyError``/``RuntimeError`` strings. Layer-specific taxonomies
(``qts.execution.errors``, ``qts.runtime.errors``) extend these bases.
"""

from __future__ import annotations


class QTSError(Exception):
    """Base class for all quant-trading-system domain and runtime errors."""


class QTSConfigurationError(QTSError):
    """Configuration is structurally or semantically invalid."""


class QTSInvariantError(QTSError):
    """A domain or runtime invariant that should always hold was violated."""


class QTSRuntimeError(QTSError):
    """A runtime orchestration failure not tied to a single domain invariant."""


__all__ = [
    "QTSConfigurationError",
    "QTSError",
    "QTSInvariantError",
    "QTSRuntimeError",
]
