"""Backtest run configuration and stable run identity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.ids import InstrumentId

_SUPPORTED_MARKET_DATA_SOURCES = frozenset({"local_historical"})


@dataclass(frozen=True, slots=True)
class CostModelConfig:
    """Explicit backtest cost model settings."""

    fixed_commission_per_contract: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")

    def __post_init__(self) -> None:
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
        return {
            "fixed_commission_per_contract": str(self.fixed_commission_per_contract),
            "slippage_bps": str(self.slippage_bps),
        }


@dataclass(frozen=True, slots=True)
class RiskConfig:
    """Backtest risk settings."""

    max_notional: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_notional", Decimal(str(self.max_notional)))
        if self.max_notional <= Decimal("0"):
            raise ValueError("max_notional must be positive")

    def to_payload(self) -> dict[str, str]:
        return {"max_notional": str(self.max_notional)}


@dataclass(frozen=True, slots=True)
class RollPolicyConfig:
    """Continuous futures roll policy for config-driven backtest runs."""

    enabled: bool = False
    method: str = "highest_volume"

    def __post_init__(self) -> None:
        normalized = self.method.strip().lower()
        if normalized != "highest_volume":
            raise ValueError("roll_policy.method must be highest_volume")
        object.__setattr__(self, "method", normalized)

    def to_payload(self) -> dict[str, object]:
        return {"enabled": self.enabled, "method": self.method}


@dataclass(frozen=True, slots=True)
class BacktestMarketDataReference:
    """Market data source reference for one backtest run."""

    config_path: Path | None = None
    catalog: str | None = None
    source: str = "local_historical"

    def __post_init__(self) -> None:
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
        return self.config_path is not None and self.catalog is not None

    def to_payload(self) -> dict[str, str] | None:
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
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("strategy config must be a mapping")
        return cls._parse_payload(payload)

    def to_payload(self) -> dict[str, Any]:
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
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("backtest config must be a mapping")
        cost_payload = payload.get("cost_model", {})
        risk_payload = payload.get("risk_config", {})
        if not isinstance(cost_payload, dict):
            raise ValueError("cost_model must be a mapping")
        if not isinstance(risk_payload, dict):
            raise ValueError("risk_config must be a mapping")
        roll_payload = payload.get("roll_policy", {})
        if not isinstance(roll_payload, dict):
            raise ValueError("roll_policy must be a mapping")
        strategy_params = payload.get("strategy_params", {})
        instrument_ids_payload = payload.get("instrument_ids", {})
        if not isinstance(strategy_params, dict):
            raise ValueError("strategy_params must be a mapping")
        if not isinstance(instrument_ids_payload, dict):
            raise ValueError("instrument_ids must be a mapping")
        dataset_root = (
            Path(str(payload["dataset_root"])) if payload.get("dataset_root") is not None else None
        )
        strategy_config_path = (
            Path(str(payload["strategy_config"]))
            if payload.get("strategy_config") is not None
            else None
        )
        if strategy_config_path is not None:
            if "strategy_class" in payload or "strategy_params" in payload:
                raise ValueError(
                    "strategy_config must not be combined with strategy_class or strategy_params"
                )
            strategy = BacktestStrategyConfig.from_yaml(strategy_config_path)
            strategy_class = strategy.class_path
            strategy_params = dict(strategy.params)
        else:
            strategy = None
            strategy_class = str(payload["strategy_class"])
        return cls(
            roots=tuple(payload["roots"]),
            symbols=tuple(payload["symbols"]),
            start=cls._parse_datetime(str(payload["start"])),
            end=cls._parse_datetime(str(payload["end"])),
            timeframe=payload["timeframe"],
            initial_cash=Decimal(str(payload["initial_cash"])),
            strategy_class=strategy_class,
            dataset_root=dataset_root,
            market_data=cls._parse_market_data_reference(payload.get("market_data")),
            historical_data=cls._parse_historical_data_reference(payload.get("historical_data")),
            strategy_config_path=strategy_config_path,
            strategy=strategy,
            strategy_params=strategy_params,
            instrument_ids={
                str(symbol): InstrumentId(str(instrument_id))
                for symbol, instrument_id in instrument_ids_payload.items()
            },
            cost_model=CostModelConfig(
                fixed_commission_per_contract=Decimal(
                    str(cost_payload.get("fixed_commission_per_contract", "0"))
                ),
                slippage_bps=Decimal(str(cost_payload.get("slippage_bps", "0"))),
            ),
            risk_config=RiskConfig(
                max_notional=Decimal(str(risk_payload.get("max_notional", "1")))
            ),
            roll_policy=RollPolicyConfig(
                enabled=bool(roll_payload.get("enabled", False)),
                method=str(roll_payload.get("method", "highest_volume")),
            ),
            warmup_bars=int(payload.get("warmup_bars", 0)),
        )

    @property
    def config_hash(self) -> str:
        return self._stable_hash(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
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
    def _parse_datetime(value: datetime | str) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("datetime values must be timezone-aware")
        return parsed.astimezone(UTC)

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("instrument_ids must not contain empty symbols")
        return normalized

    @staticmethod
    def _parse_market_data_reference(payload: object) -> BacktestMarketDataReference:
        if payload is None:
            return BacktestMarketDataReference()
        if not isinstance(payload, dict):
            raise ValueError("market_data must be a mapping")
        return BacktestMarketDataReference(
            config_path=Path(str(payload["config"])),
            catalog=str(payload["catalog"]),
            source=str(payload.get("source", "local_historical")),
        )

    @staticmethod
    def _parse_historical_data_reference(payload: object) -> BacktestMarketDataReference:
        if payload is None:
            return BacktestMarketDataReference()
        if not isinstance(payload, dict):
            raise ValueError("historical_data must be a mapping")
        return BacktestMarketDataReference(
            config_path=Path(str(payload["config"])),
            catalog=str(payload["catalog"]),
            source=str(payload.get("source", "local_historical")),
        )

    @staticmethod
    def _stable_hash(payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


__all__ = [
    "BacktestHistoricalDataReference",
    "BacktestMarketDataReference",
    "BacktestRunConfig",
    "BacktestStrategyConfig",
    "CostModelConfig",
    "RiskConfig",
    "RollPolicyConfig",
]
