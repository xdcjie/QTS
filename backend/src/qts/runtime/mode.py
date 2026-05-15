"""Runtime mode and environment vocabulary."""

from __future__ import annotations

from enum import StrEnum


class RuntimeMode(StrEnum):
    """Execution mode for one runtime run."""

    BACKTEST = "backtest"
    PAPER_BROKER = "paper_broker"
    PAPER_SIMULATED = "paper_simulated"
    LIVE_OBSERVATION = "live_observation"
    LIVE = "live"
    OBSERVATION = "observation"

    @classmethod
    def from_value(cls, value: RuntimeMode | str) -> RuntimeMode:
        """Normalize runtime mode labels."""
        if isinstance(value, cls):
            return value
        normalized = value.strip().lower().replace("-", "_")
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported runtime mode: {value}") from exc


class MarketDataEnvironment(StrEnum):
    """Temporal market-data environment for a runtime run."""

    REPLAY = "replay"
    REALTIME = "realtime"

    @classmethod
    def from_value(
        cls, value: MarketDataEnvironment | str | None, *, mode: RuntimeMode
    ) -> MarketDataEnvironment:
        """Normalize market-data environment with mode-aware defaults."""
        if isinstance(value, cls):
            return value
        if value is None:
            if mode is RuntimeMode.BACKTEST:
                return cls.REPLAY
            return cls.REALTIME
        return cls(value.strip().lower().replace("-", "_"))


class ExecutionEnvironment(StrEnum):
    """Order execution environment for a runtime run."""

    SIMULATED = "simulated"
    BROKER = "broker"
    DISABLED = "disabled"

    @classmethod
    def from_value(
        cls, value: ExecutionEnvironment | str | None, *, mode: RuntimeMode
    ) -> ExecutionEnvironment:
        """Normalize execution environment with mode-aware defaults."""
        if isinstance(value, cls):
            return value
        if value is None:
            if mode in {RuntimeMode.BACKTEST, RuntimeMode.PAPER_SIMULATED}:
                return cls.SIMULATED
            if mode in {RuntimeMode.OBSERVATION, RuntimeMode.LIVE_OBSERVATION}:
                return cls.DISABLED
            return cls.BROKER
        return cls(value.strip().lower().replace("-", "_"))


class AccountEnvironment(StrEnum):
    """Funding account environment for a runtime run."""

    SIMULATED = "simulated"
    PAPER = "paper"
    LIVE = "live"

    @classmethod
    def from_value(
        cls, value: AccountEnvironment | str | None, *, mode: RuntimeMode
    ) -> AccountEnvironment:
        """Normalize account environment with mode-aware defaults."""
        if isinstance(value, cls):
            return value
        if value is None:
            if mode in {RuntimeMode.BACKTEST, RuntimeMode.PAPER_SIMULATED}:
                return cls.SIMULATED
            if mode is RuntimeMode.LIVE:
                return cls.LIVE
            return cls.PAPER
        return cls(value.strip().lower().replace("-", "_"))


__all__ = [
    "AccountEnvironment",
    "ExecutionEnvironment",
    "MarketDataEnvironment",
    "RuntimeMode",
]
