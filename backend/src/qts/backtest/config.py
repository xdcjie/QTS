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


@dataclass(frozen=True, slots=True)
class CostModelConfig:
    """Explicit research cost model settings."""

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
    """Continuous futures roll policy for config-driven research runs."""

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
class BacktestRunConfig:
    """Complete identity for a research backtest run."""

    dataset_root: Path
    roots: tuple[str, ...]
    symbols: tuple[str, ...]
    start: datetime
    end: datetime
    timeframe: str
    initial_cash: Decimal
    strategy_class: str
    strategy_params: dict[str, Any] = field(default_factory=dict)
    instrument_ids: dict[str, InstrumentId] = field(default_factory=dict)
    cost_model: CostModelConfig = field(default_factory=CostModelConfig)
    risk_config: RiskConfig = field(default_factory=lambda: RiskConfig(max_notional=Decimal("1")))
    roll_policy: RollPolicyConfig = field(default_factory=RollPolicyConfig)
    warmup_bars: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "roots", tuple(self.roots))
        object.__setattr__(self, "symbols", tuple(self.symbols))
        object.__setattr__(self, "initial_cash", Decimal(str(self.initial_cash)))
        object.__setattr__(
            self,
            "instrument_ids",
            {
                _normalize_symbol(symbol): (
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
        return cls(
            dataset_root=Path(str(payload["dataset_root"])),
            roots=tuple(payload["roots"]),
            symbols=tuple(payload["symbols"]),
            start=_parse_datetime(str(payload["start"])),
            end=_parse_datetime(str(payload["end"])),
            timeframe=payload["timeframe"],
            initial_cash=Decimal(str(payload["initial_cash"])),
            strategy_class=payload["strategy_class"],
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
        return _stable_hash(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        return {
            "dataset_root": str(self.dataset_root),
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


def _parse_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("datetime values must be timezone-aware")
    return parsed.astimezone(UTC)


def _normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("instrument_ids must not contain empty symbols")
    return normalized


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


__all__ = ["BacktestRunConfig", "CostModelConfig", "RiskConfig", "RollPolicyConfig"]
