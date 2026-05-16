"""Backtest application DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BacktestRequestDTO:
    """Stable application request for starting a backtest."""

    config_path: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.config_path.strip():
            raise ValueError("config_path must not be empty")
        path = Path(self.config_path)
        if not path.exists():
            raise ValueError(f"config file does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"config_path must be a file: {path}")


@dataclass(frozen=True, slots=True)
class BacktestRunDTO:
    """Stable application response for a submitted backtest."""

    run_id: str
    config_path: str
    status: str
    summary_path: str
    manifest_path: str | None = None
    report_hash: str | None = None


@dataclass(frozen=True, slots=True)
class BacktestStrategyOptionDTO:
    """Configured backtest option exposed to UI/API clients."""

    label: str
    config_path: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.label.strip():
            raise ValueError("label must not be empty")
        if not self.config_path.strip():
            raise ValueError("config_path must not be empty")


__all__ = ["BacktestRequestDTO", "BacktestRunDTO", "BacktestStrategyOptionDTO"]
