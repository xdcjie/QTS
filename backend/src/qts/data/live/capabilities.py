"""Deprecated live capabilities exports.

Canonical capability contract now lives in :mod:`qts.data.capabilities`.
"""

from __future__ import annotations

import warnings

from qts.data.capabilities import LiveFeedTimeframeSet, MarketDataFeedCapabilities

# Keep backward-compatible names for one release only.
warnings.warn(
    "qts.data.live.capabilities.* is deprecated and will be removed in the next release; "
    "use qts.data.capabilities instead.",
    DeprecationWarning,
    stacklevel=2,
)

FeedCapabilities = MarketDataFeedCapabilities


__all__ = ["FeedCapabilities", "LiveFeedTimeframeSet"]
