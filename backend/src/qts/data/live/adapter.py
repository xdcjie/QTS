"""Live market-data protocols.

Canonical protocol definitions now live in :mod:`qts.data.interfaces`.
This module is a temporary compatibility layer for existing imports.
"""

from __future__ import annotations

import warnings

from qts.data.interfaces import MarketDataAdapter, StreamingFeedAdapter

# Keep backward-compatible names for one release only.
warnings.warn(
    "qts.data.live.adapter.* is deprecated and will be removed in the next release; "
    "use qts.data.interfaces instead.",
    DeprecationWarning,
    stacklevel=2,
)


LiveFeedAdapter = StreamingFeedAdapter


__all__ = ["LiveFeedAdapter", "MarketDataAdapter", "StreamingFeedAdapter"]
