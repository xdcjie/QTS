"""Deprecated live event exports.

Shared DTOs now live in :mod:`qts.data.events`.
"""

from __future__ import annotations

import warnings

from qts.data.events import (
    MarketDataPayload as LiveFeedPayload,
)
from qts.data.events import (
    MarketDataSourceEvent as LiveFeedEvent,
)
from qts.data.events import (
    MarketDataSourceFailure as LiveFeedFailure,
)
from qts.data.events import (
    MarketDataSubscribed,
)
from qts.data.events import (
    MarketDataSubscription as FeedSubscription,
)

# Keep backward-compatible names for one release only.
warnings.warn(
    "qts.data.live.events.* is deprecated and will be removed in the next release; "
    "use qts.data.events instead.",
    DeprecationWarning,
    stacklevel=2,
)


__all__ = [
    "FeedSubscription",
    "MarketDataSubscribed",
    "LiveFeedEvent",
    "LiveFeedFailure",
    "LiveFeedPayload",
]
