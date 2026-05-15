from qts.data.capabilities import MarketDataFeedCapabilities
from qts.data.events import (
    MarketDataSourceEvent,
    MarketDataSourceFailure,
    MarketDataSubscribed,
    MarketDataSubscription,
)
from qts.data.historical import HistoricalMarketDataAdapter
from qts.data.interfaces import MarketDataAdapter, StreamingFeedAdapter
from qts.data.live.reconnect import ReconnectPolicy
from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
from qts.data.provenance import DatasetMetadata
from qts.data.subscriptions import (
    LogicalSubscription,
    LogicalSubscriptionKey,
    PhysicalSubscriptionKey,
    SourceStreamType,
    logical_key,
    plan_physical_subscription,
)
from qts.data.validation_report import (
    DataValidationError,
    DataValidationIssue,
    DataValidationReport,
)

__all__ = [
    "MarketDataAdapter",
    "StreamingFeedAdapter",
    "MarketDataPermissionEvent",
    "MarketDataPermissionState",
    "HistoricalMarketDataAdapter",
    "MarketDataFeedCapabilities",
    "MarketDataSourceEvent",
    "MarketDataSourceFailure",
    "MarketDataSubscription",
    "MarketDataSubscribed",
    "FeedCapabilities",
    "FeedSubscription",
    "LiveFeedAdapter",
    "LiveFeedEvent",
    "LiveFeedFailure",
    "ReconnectPolicy",
    "DataValidationError",
    "DataValidationIssue",
    "DataValidationReport",
    "DatasetMetadata",
    "LogicalSubscription",
    "LogicalSubscriptionKey",
    "PhysicalSubscriptionKey",
    "SourceStreamType",
    "logical_key",
    "plan_physical_subscription",
]

# Backward-compatible aliases for pre-migration callers.
FeedCapabilities = MarketDataFeedCapabilities
FeedSubscription = MarketDataSubscription
LiveFeedAdapter = StreamingFeedAdapter
LiveFeedEvent = MarketDataSourceEvent
LiveFeedFailure = MarketDataSourceFailure
