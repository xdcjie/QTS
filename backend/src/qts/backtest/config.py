"""Backtest run configuration and stable run identity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_hash
from qts.core.ids import InstrumentId

_SUPPORTED_MARKET_DATA_SOURCES = frozenset({"local_historical"})


@dataclass(frozen=True, slots=True)
class CostModelConfig:
    """Explicit backtest cost model settings."""

    fixed_commission_per_contract: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        object.__setattr__(
            self,
            "fixed_commission_per_contract",
            Decimal(str(self.fixed_commission_per_contract)),
        )
        object.__setattr__(self, "slippage_bps", Decimal(str(self.slippage_bps)))
        if self.fixed_commission_per_contract < Decimal("0"):
            raise ValueError("fixed_commission_per_contract must be non-negative")
        if self.slippage_bps < Decimal("0"):
            raise ValueError("slippage_bps must be non-negative")

    def to_payload(self) -> dict[str, str]:
        """Perform to_payload."""
        return {
            "fixed_commission_per_contract": str(self.fixed_commission_per_contract),
            "slippage_bps": str(self.slippage_bps),
        }


@dataclass(frozen=True, slots=True)
class RiskConfig:
    """Backtest risk settings."""

    max_notional: Decimal

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        object.__setattr__(self, "max_notional", Decimal(str(self.max_notional)))
        if self.max_notional <= Decimal("0"):
            raise ValueError("max_notional must be positive")

    def to_payload(self) -> dict[str, str]:
        """Perform to_payload."""
        return {"max_notional": str(self.max_notional)}


@dataclass(frozen=True, slots=True)
class RollPolicyConfig:
    """Continuous futures roll policy for config-driven backtest runs."""

    enabled: bool = False
    method: str = "highest_volume"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        normalized = self.method.strip().lower()
        if normalized != "highest_volume":
            raise ValueError("roll_policy.method must be highest_volume")
        object.__setattr__(self, "method", normalized)

    def to_payload(self) -> dict[str, object]:
        """Perform to_payload."""
        return {"enabled": self.enabled, "method": self.method}


@dataclass(frozen=True, slots=True)
class BacktestMarketDataReference:
    """Market data source reference for one backtest run."""

    config_path: Path | None = None
    catalog: str | None = None
    source: str = "local_historical"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.config_path is not None:
            object.__setattr__(self, "config_path", Path(self.config_path))
        source = self.source.strip().lower()
        if not source:
            raise ValueError("market_data.source must not be empty")
        if source not in _SUPPORTED_MARKET_DATA_SOURCES:
            raise ValueError(f"unsupported market_data.source: {self.source}")
        object.__setattr__(self, "source", source)
        if self.catalog is not None:
            normalized = self.catalog.strip()
            if not normalized:
                raise ValueError("market_data.catalog must not be empty")
            object.__setattr__(self, "catalog", normalized)
        if (self.config_path is None) != (self.catalog is None):
            raise ValueError("market_data config and catalog must be provided together")

    @property
    def is_configured(self) -> bool:
        """Perform is_configured."""
        return self.config_path is not None and self.catalog is not None

    def to_payload(self) -> dict[str, str] | None:
        """Perform to_payload."""
        if not self.is_configured:
            return None
        if self.config_path is None or self.catalog is None:
            raise RuntimeError("market data reference is partially configured")
        return {"source": self.source, "config": str(self.config_path), "catalog": self.catalog}


BacktestHistoricalDataReference = BacktestMarketDataReference


@dataclass(frozen=True, slots=True)
class BacktestStrategyConfig:
    """Configured strategy instance referenced by a backtest run."""

    class_path: str
    params: dict[str, Any] = field(default_factory=dict)
    strategy_id: str | None = None
    account_id: str | None = None
    allocation: Decimal = Decimal("1")
    enabled: bool = True

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.class_path.strip():
            raise ValueError("strategy class_path must not be empty")
        object.__setattr__(self, "params", dict(self.params))
        object.__setattr__(self, "allocation", Decimal(str(self.allocation)))
        if self.strategy_id is not None and not self.strategy_id.strip():
            raise ValueError("strategy_id must not be empty")
        if self.account_id is not None and not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if self.allocation < Decimal("0"):
            raise ValueError("strategy allocation must be non-negative")

    @classmethod
    def from_yaml(cls, path: Path) -> BacktestStrategyConfig:
        """Perform from_yaml."""
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("strategy config must be a mapping")
        return cls._parse_payload(payload)

    def to_payload(self) -> dict[str, Any]:
        """Perform to_payload."""
        return {
            "strategy_id": self.strategy_id,
            "class_path": self.class_path,
            "account_id": self.account_id,
            "allocation": str(self.allocation),
            "enabled": self.enabled,
            "params": self.params,
        }

    @classmethod
    def _parse_payload(cls, payload: dict[str, Any]) -> BacktestStrategyConfig:
        """Perform _parse_payload."""
        params = payload.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("strategy params must be a mapping")
        return cls(
            strategy_id=(
                str(payload["strategy_id"]) if payload.get("strategy_id") is not None else None
            ),
            class_path=str(payload["class_path"]),
            account_id=(
                str(payload["account_id"]) if payload.get("account_id") is not None else None
            ),
            allocation=Decimal(str(payload.get("allocation", "1"))),
            enabled=bool(payload.get("enabled", True)),
            params=params,
        )


@dataclass(frozen=True, slots=True)
class BacktestRunConfig:
    """Complete identity for a backtest run."""

    roots: tuple[str, ...]
    symbols: tuple[str, ...]
    start: datetime
    end: datetime
    timeframe: str
    initial_cash: Decimal
    strategy_class: str = ""
    dataset_root: Path | None = None
    market_data: BacktestMarketDataReference = field(default_factory=BacktestMarketDataReference)
    historical_data: BacktestMarketDataReference = field(
        default_factory=BacktestMarketDataReference
    )
    strategy_config_path: Path | None = None
    strategy: BacktestStrategyConfig | None = None
    strategy_params: dict[str, Any] = field(default_factory=dict)
    instrument_ids: dict[str, InstrumentId] = field(default_factory=dict)
    cost_model: CostModelConfig = field(default_factory=CostModelConfig)
    risk_config: RiskConfig = field(default_factory=lambda: RiskConfig(max_notional=Decimal("1")))
    roll_policy: RollPolicyConfig = field(default_factory=RollPolicyConfig)
    warmup_bars: int = 0

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.dataset_root is not None:
            object.__setattr__(self, "dataset_root", Path(self.dataset_root))
        if self.strategy_config_path is not None:
            object.__setattr__(self, "strategy_config_path", Path(self.strategy_config_path))
        if not isinstance(self.market_data, BacktestMarketDataReference):
            object.__setattr__(
                self,
                "market_data",
                BacktestMarketDataReference(**self.market_data),
            )
        if not isinstance(self.historical_data, BacktestMarketDataReference):
            object.__setattr__(
                self,
                "historical_data",
                BacktestMarketDataReference(**self.historical_data),
            )
        if self.market_data.is_configured and self.historical_data.is_configured:
            if self.market_data.to_payload() != self.historical_data.to_payload():
                raise ValueError("market_data and historical_data references must match")
        elif self.historical_data.is_configured:
            object.__setattr__(self, "market_data", self.historical_data)
        elif self.market_data.is_configured:
            object.__setattr__(self, "historical_data", self.market_data)
        if self.strategy is not None and not isinstance(self.strategy, BacktestStrategyConfig):
            object.__setattr__(self, "strategy", BacktestStrategyConfig(**self.strategy))
        object.__setattr__(self, "roots", tuple(self.roots))
        object.__setattr__(self, "symbols", tuple(self.symbols))
        object.__setattr__(self, "initial_cash", Decimal(str(self.initial_cash)))
        object.__setattr__(self, "strategy_params", dict(self.strategy_params))
        if self.strategy is not None:
            object.__setattr__(self, "strategy_class", self.strategy.class_path)
            object.__setattr__(self, "strategy_params", dict(self.strategy.params))
        object.__setattr__(
            self,
            "instrument_ids",
            {
                self._normalize_symbol(symbol): (
                    instrument_id
                    if isinstance(instrument_id, InstrumentId)
                    else InstrumentId(str(instrument_id))
                )
                for symbol, instrument_id in self.instrument_ids.items()
            },
        )
        if not self.roots:
            raise ValueError("roots must not be empty")
        if not all(root.strip() for root in self.roots):
            raise ValueError("roots must not contain empty values")
        if not self.symbols:
            raise ValueError("symbols must not be empty")
        if self.start >= self.end:
            raise ValueError("date range must have start before end")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if self.initial_cash <= Decimal("0"):
            raise ValueError("initial_cash must be positive")
        if not self.strategy_class.strip():
            raise ValueError("strategy_class must not be empty")
        if self.warmup_bars < 0:
            raise ValueError("warmup_bars must be non-negative")
        if self.dataset_root is None and not self.market_data.is_configured:
            raise ValueError("market_data or dataset_root must be configured")

    @classmethod
    def from_yaml(cls, path: Path) -> BacktestRunConfig:
        """Perform from_yaml."""
        from qts.backtest.config_loader import BacktestConfigLoader

        return BacktestConfigLoader.from_path(path)

    @property
    def config_hash(self) -> str:
        """Perform config_hash."""
        return stable_json_hash(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        """Perform to_payload."""
        payload = {
            "roots": list(self.roots),
            "symbols": list(self.symbols),
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "timeframe": self.timeframe,
            "initial_cash": str(self.initial_cash),
            "strategy_class": self.strategy_class,
            "strategy_params": self.strategy_params,
            "instrument_ids": {
                symbol: instrument_id.value
                for symbol, instrument_id in sorted(self.instrument_ids.items())
            },
            "cost_model": self.cost_model.to_payload(),
            "risk_config": self.risk_config.to_payload(),
            "roll_policy": self.roll_policy.to_payload(),
            "warmup_bars": self.warmup_bars,
        }
        if self.dataset_root is not None:
            payload["dataset_root"] = str(self.dataset_root)
        market_data = self.market_data.to_payload()
        if market_data is not None:
            payload["market_data"] = market_data
        if self.strategy_config_path is not None:
            payload["strategy_config"] = str(self.strategy_config_path)
        if self.strategy is not None:
            payload["strategy"] = self.strategy.to_payload()
        return payload

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Perform _normalize_symbol."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("instrument_ids must not contain empty symbols")
        return normalized


__all__ = [
    "BacktestHistoricalDataReference",
    "BacktestMarketDataReference",
    "BacktestRunConfig",
    "BacktestStrategyConfig",
    "CostModelConfig",
    "RiskConfig",
    "RollPolicyConfig",
]
