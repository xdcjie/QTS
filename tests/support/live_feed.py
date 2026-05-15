"""Legacy test support shim.

Keep this module for compatibility with existing tests and scripts that still import
``tests.support.live_feed``.
"""

from qts.testing.fakes.market_data import FakeLiveFeedAdapter

__all__ = ["FakeLiveFeedAdapter"]
