"""Online trailing session regime features."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from statistics import median
from typing import Protocol
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.domain.return_statistics import compound_return, mean_return, realized_volatility

REGIME_RULES = frozenset({"off", "hard14", "hard_churn225", "hard14_ccvol17"})
UNREADY_POLICIES = frozenset({"allow", "block"})


@dataclass(frozen=True, slots=True)
class SessionRegimeGateConfig:
    """Configuration for a trailing completed-session regime gate."""

    rule: str = "off"
    symbols: tuple[str, ...] = ()
    timeframe: str = "15m"
    lookback_sessions: int = 120
    min_history_sessions: int = 120
    unready_policy: str = "block"
    asia_start_et_hour: int = 20
    asia_end_et_hour: int = 2
    range_min: Decimal = Decimal("0.015")
    asia_share_max: Decimal = Decimal("0.14")
    min_return_floor: Decimal = Decimal("-0.15")
    mean_churn_min: Decimal = Decimal("2.25")
    mean_realized_vol_max: Decimal = Decimal("0.017")

    def __post_init__(self) -> None:
        rule = str(self.rule).strip().lower()
        if rule not in REGIME_RULES:
            raise ValueError(f"rule must be one of {sorted(REGIME_RULES)}")
        object.__setattr__(self, "rule", rule)
        unready_policy = str(self.unready_policy).strip().lower()
        if unready_policy not in UNREADY_POLICIES:
            raise ValueError(f"unready_policy must be one of {sorted(UNREADY_POLICIES)}")
        object.__setattr__(self, "unready_policy", unready_policy)
        symbols = (self.symbols,) if isinstance(self.symbols, str) else tuple(self.symbols)
        symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if rule != "off" and not symbols:
            raise ValueError("symbols must be non-empty when regime gate is enabled")
        if any(not symbol for symbol in symbols):
            raise ValueError("symbols must not contain empty values")
        object.__setattr__(self, "symbols", symbols)
        if self.lookback_sessions <= 0:
            raise ValueError("lookback_sessions must be positive")
        if self.min_history_sessions <= 0:
            raise ValueError("min_history_sessions must be positive")
        if self.min_history_sessions > self.lookback_sessions:
            raise ValueError("min_history_sessions must be <= lookback_sessions")
        if not self.timeframe.strip():
            raise ValueError("timeframe must be non-empty")
        for name in (
            "range_min",
            "asia_share_max",
            "min_return_floor",
            "mean_churn_min",
            "mean_realized_vol_max",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                object.__setattr__(self, name, Decimal(str(value)))
        if self.range_min <= Decimal("0"):
            raise ValueError("range_min must be positive")
        if not Decimal("0") <= self.asia_share_max <= Decimal("1"):
            raise ValueError("asia_share_max must be between 0 and 1")
        if self.mean_churn_min <= Decimal("0"):
            raise ValueError("mean_churn_min must be positive")
        if self.mean_realized_vol_max <= Decimal("0"):
            raise ValueError("mean_realized_vol_max must be positive")
        if not (0 <= self.asia_start_et_hour < 24):
            raise ValueError("asia_start_et_hour must be 0..23")
        if not (0 <= self.asia_end_et_hour <= 24):
            raise ValueError("asia_end_et_hour must be 0..24")
        if self.asia_start_et_hour == self.asia_end_et_hour:
            raise ValueError("asia_start_et_hour must differ from asia_end_et_hour")


@dataclass(frozen=True, slots=True)
class CompletedRegimeSession:
    """One completed session's regime evidence."""

    range_pct: Decimal
    asia_volume_share: Decimal
    close_to_close_return: Decimal
    churn: Decimal | None


@dataclass(frozen=True, slots=True)
class SessionRegimeSnapshot:
    """Trailing regime evidence aggregated across configured symbols."""

    mean_range_pct: Decimal
    mean_asia_share: Decimal
    min_trailing_return: Decimal
    mean_median_churn: Decimal | None
    mean_realized_vol: Decimal | None


@dataclass(slots=True)
class _RegimeAccumulator:
    session_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    total_volume: Decimal
    asia_volume: Decimal

    @classmethod
    def from_bar(cls, bar: Bar, *, is_asia: bool) -> _RegimeAccumulator:
        return cls(
            session_id=str(bar.session_id),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            total_volume=bar.volume,
            asia_volume=bar.volume if is_asia else Decimal("0"),
        )

    def update(self, bar: Bar, *, is_asia: bool) -> None:
        self.high = max(self.high, bar.high)
        self.low = min(self.low, bar.low)
        self.close = bar.close
        self.total_volume += bar.volume
        if is_asia:
            self.asia_volume += bar.volume

    def complete(self, previous_close: Decimal | None) -> CompletedRegimeSession | None:
        if self.open <= Decimal("0") or previous_close is None or previous_close <= Decimal("0"):
            return None
        range_pct = (self.high - self.low) / self.open
        close_to_close_return = (self.close - previous_close) / previous_close
        abs_return = abs(close_to_close_return)
        asia_share = (
            self.asia_volume / self.total_volume
            if self.total_volume > Decimal("0")
            else Decimal("0")
        )
        return CompletedRegimeSession(
            range_pct=range_pct,
            asia_volume_share=asia_share,
            close_to_close_return=close_to_close_return,
            churn=range_pct / abs_return if abs_return > Decimal("0") else None,
        )


@dataclass(slots=True)
class _RegimeSymbolState:
    current: _RegimeAccumulator | None = None
    previous_close: Decimal | None = None
    completed: deque[CompletedRegimeSession] = field(default_factory=deque)


class _SessionRegimeGateConfigLike(Protocol):
    @property
    def rule(self) -> str: ...

    @property
    def symbols(self) -> tuple[str, ...]: ...

    @property
    def lookback_sessions(self) -> int: ...

    @property
    def min_history_sessions(self) -> int: ...

    @property
    def unready_policy(self) -> str: ...

    @property
    def asia_start_et_hour(self) -> int: ...

    @property
    def asia_end_et_hour(self) -> int: ...

    @property
    def range_min(self) -> Decimal: ...

    @property
    def asia_share_max(self) -> Decimal: ...

    @property
    def min_return_floor(self) -> Decimal: ...

    @property
    def mean_churn_min(self) -> Decimal: ...

    @property
    def mean_realized_vol_max(self) -> Decimal: ...


class TrailingSessionRegimeGate:
    """Online trailing regime gate using completed sessions only."""

    def __init__(self, config: _SessionRegimeGateConfigLike) -> None:
        self._config = config
        self._states = {symbol: _RegimeSymbolState() for symbol in config.symbols}
        self._et_tz = ZoneInfo("US/Eastern")

    def update_bar(self, symbol: str, bar: Bar) -> None:
        """Update current-session evidence and finalize only on session change."""
        if self._config.rule == "off":
            return
        state = self._states.get(symbol.upper())
        if state is None:
            return
        is_asia = self._is_asia_bar(bar)
        session_id = str(bar.session_id)
        if state.current is None:
            state.current = _RegimeAccumulator.from_bar(bar, is_asia=is_asia)
            return
        if state.current.session_id != session_id:
            self._finalize_current(state)
            state.current = _RegimeAccumulator.from_bar(bar, is_asia=is_asia)
            return
        state.current.update(bar, is_asia=is_asia)

    def allows_new_entries(self) -> bool:
        """Return whether new entries are allowed by the trailing regime rule."""
        if self._config.rule == "off":
            return True
        snapshot = self.snapshot()
        if snapshot is None:
            return self._config.unready_policy == "allow"
        return not self.blocks(snapshot)

    def snapshot(self) -> SessionRegimeSnapshot | None:
        """Return the completed-session snapshot, or None before warmup."""
        if any(
            len(state.completed) < self._config.min_history_sessions
            for state in self._states.values()
        ):
            return None

        ranges: list[Decimal] = []
        asia_shares: list[Decimal] = []
        trailing_returns: list[Decimal] = []
        median_churns: list[Decimal] = []
        realized_vols: list[Decimal] = []

        for state in self._states.values():
            sessions = tuple(state.completed)[-self._config.lookback_sessions :]
            returns = tuple(session.close_to_close_return for session in sessions)
            ranges.append(mean_return(session.range_pct for session in sessions))
            asia_shares.append(mean_return(session.asia_volume_share for session in sessions))
            trailing_returns.append(compound_return(returns))
            churns = tuple(session.churn for session in sessions if session.churn is not None)
            if churns:
                median_churns.append(median(churns))
            realized_vols.append(realized_volatility(returns))

        return SessionRegimeSnapshot(
            mean_range_pct=mean_return(ranges),
            mean_asia_share=mean_return(asia_shares),
            min_trailing_return=min(trailing_returns),
            mean_median_churn=mean_return(median_churns) if median_churns else None,
            mean_realized_vol=mean_return(realized_vols) if realized_vols else None,
        )

    def blocks(self, snapshot: SessionRegimeSnapshot) -> bool:
        """Return whether the configured rule identifies a blocked regime."""
        hard14 = (
            snapshot.mean_range_pct >= self._config.range_min
            and snapshot.mean_asia_share <= self._config.asia_share_max
            and snapshot.min_trailing_return > self._config.min_return_floor
        )
        if not hard14:
            return False
        if self._config.rule == "hard14":
            return True
        if self._config.rule == "hard_churn225":
            return (
                snapshot.mean_median_churn is not None
                and snapshot.mean_median_churn >= self._config.mean_churn_min
            )
        if self._config.rule == "hard14_ccvol17":
            return (
                snapshot.mean_realized_vol is not None
                and snapshot.mean_realized_vol <= self._config.mean_realized_vol_max
            )
        return False

    def _finalize_current(self, state: _RegimeSymbolState) -> None:
        if state.current is None:
            return
        completed = state.current.complete(state.previous_close)
        state.previous_close = state.current.close
        if completed is None:
            return
        state.completed.append(completed)
        while len(state.completed) > self._config.lookback_sessions:
            state.completed.popleft()

    def _is_asia_bar(self, bar: Bar) -> bool:
        et_dt = bar.start_time.astimezone(self._et_tz)
        minutes = et_dt.hour * 60 + et_dt.minute
        start = self._config.asia_start_et_hour * 60
        end = self._config.asia_end_et_hour * 60
        if start < end:
            return start <= minutes < end
        return minutes >= start or minutes < end


__all__ = [
    "CompletedRegimeSession",
    "REGIME_RULES",
    "SessionRegimeGateConfig",
    "SessionRegimeSnapshot",
    "TrailingSessionRegimeGate",
    "UNREADY_POLICIES",
]
