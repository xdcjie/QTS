"""Session-aware intraday PnL calculator owned by the risk layer."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding


class IntradayPnlCalculator:
    """Compute session intraday PnL = realized-since-session-open + unrealized.

    Stateful and session-aware. ``start_session`` captures the realized-PnL
    baseline at the session open from the current holdings; ``compute`` returns
    the realized PnL accrued since that baseline plus the current unrealized
    PnL marked to ``marks``. Supplying a new ``session_id`` resets the realized
    baseline, so each session's intraday loss window starts at zero realized
    PnL. Unrealized PnL is always measured against the live average cost.
    """

    def __init__(self) -> None:
        """Initialise with no session captured."""
        self._session_id: str | None = None
        self._realized_baseline: dict[InstrumentId, Decimal] = {}

    @property
    def session_id(self) -> str | None:
        """Return the currently tracked session id, if any."""
        return self._session_id

    def start_session(
        self,
        session_id: str,
        holdings: Mapping[InstrumentId, Holding],
    ) -> None:
        """Capture the realized-PnL baseline at the open of ``session_id``."""
        self._session_id = session_id
        self._realized_baseline = {
            instrument_id: holding.realized_pnl for instrument_id, holding in holdings.items()
        }

    def compute(
        self,
        *,
        session_id: str,
        holdings: Mapping[InstrumentId, Holding],
        marks: Mapping[InstrumentId, Decimal],
        multipliers: Mapping[InstrumentId, Decimal],
    ) -> Decimal:
        """Return intraday PnL for ``session_id``, resetting the window on change."""
        if session_id != self._session_id:
            self.start_session(session_id, holdings)
        realized = Decimal("0")
        unrealized = Decimal("0")
        for instrument_id, holding in holdings.items():
            baseline = self._realized_baseline.get(instrument_id, Decimal("0"))
            realized += holding.realized_pnl - baseline
            mark = marks.get(instrument_id)
            if mark is None or holding.quantity == Decimal("0"):
                continue
            multiplier = multipliers.get(instrument_id, Decimal("1"))
            unrealized += holding.unrealized_pnl(mark, multiplier)
        return realized + unrealized


__all__ = ["IntradayPnlCalculator"]
