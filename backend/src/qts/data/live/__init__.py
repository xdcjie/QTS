"""Live market-data compatibility surface.

Shared market-data contracts are now exposed from:
- :mod:`qts.data.capabilities`
- :mod:`qts.data.events`
- :mod:`qts.data.interfaces`

This module keeps legacy imports alive for one release.
"""

from __future__ import annotations

from qts.data.capabilities import MarketDataFeedCapabilities as FeedCapabilities
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
from qts.data.interfaces import MarketDataAdapter
from qts.data.interfaces import StreamingFeedAdapter as LiveFeedAdapter
from qts.data.live.reconnect import ReconnectPolicy

__all__ = [
    "FeedCapabilities",
    "FeedSubscription",
    "LiveFeedAdapter",
    "LiveFeedEvent",
    "LiveFeedFailure",
    "LiveFeedPayload",
    "MarketDataAdapter",
    "MarketDataSubscribed",
    "ReconnectPolicy",
]
