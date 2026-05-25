"""Runtime configuration models shared by backtest, paper, and live modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_hash
from qts.core.ids import InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.reporting.backtest import dataset_metadata_payload
from qts.runtime.mode import (
    AccountEnvironment,
    ExecutionEnvironment,
    MarketDataEnvironment,
    RuntimeMode,
)
from qts.runtime.signal_policy import SignalAggregationPolicy

_SUPPORTED_MARKET_DATA_SOURCES = frozenset({"local_historical"})


@dataclass(frozen=True, slots=True)
class TradingRuntimeConfig:
    """Base runtime configuration contract for all execution modes."""

    mode: str

    def __post_init__(self) -> None:
        """Validate the runtime mode label."""
        normalized = self.mode.strip().lower()
        if not normalized:
            raise ValueError("mode must not be empty")
        object.__setattr__(self, "mode", normalized)


@dataclass(frozen=True, slots=True)
class ConfigMigrationResult:
    """Result of an explicit runtime config schema migration."""

    payload: dict[str, Any]
    from_version: str
    to_version: str
    change_log: tuple[str, ...]


class ConfigMigration:
    """Migrate runtime config payloads between explicit schema versions."""

    @classmethod
    def migrate(
        cls,
        payload: Mapping[str, Any],
        *,
        target_version: str,
    ) -> ConfigMigrationResult:
        """Return a migrated payload copy and an audit-oriented changelog."""
        from_version = cls._normalize_version(payload.get("schema_version", "1"))
        to_version = cls._normalize_version(target_version)
        migrated = cls._copy_payload(payload)
        change_log: list[str] = []

        if from_version == to_version:
            return ConfigMigrationResult(
                payload=migrated,
                from_version=from_version,
                to_version=to_version,
                change_log=(),
            )
        if (from_version, to_version) != ("1", "2"):
            raise ValueError(f"unsupported config migration: {from_version} -> {to_version}")

        cls._migrate_v1_to_v2(migrated, change_log=change_log)
        return ConfigMigrationResult(
            payload=migrated,
            from_version=from_version,
            to_version=to_version,
            change_log=tuple(change_log),
        )

    @classmethod
    def _migrate_v1_to_v2(cls, payload: dict[str, Any], *, change_log: list[str]) -> None:
        """Add explicit schema versions without changing runtime semantics."""
        payload["schema_version"] = "2"
        change_log.append("schema_version: 1 -> 2")

        risk_payload = payload.get("risk_config", {})
        if not isinstance(risk_payload, Mapping):
            raise ValueError("risk_config must be a mapping")
        risk_payload = dict(risk_payload)
        risk_version = cls._normalize_version(risk_payload.get("schema_version", "1"))
        risk_payload["schema_version"] = "2"
        payload["risk_config"] = risk_payload
        change_log.append(f"risk_config.schema_version: {risk_version} -> 2")

    @staticmethod
    def _copy_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
        """Copy the top-level payload and mapping values that migrations may edit."""
        return {
            key: dict(value) if isinstance(value, Mapping) else value
            for key, value in payload.items()
        }

    @staticmethod
    def _normalize_version(value: object) -> str:
        """Normalize schema version labels for deterministic migrations."""
        version = str(value).strip()
        if not version:
            raise ValueError("schema_version must not be empty")
        return version


@dataclass(frozen=True, slots=True)
class BacktestCostModel:
    """Backtest execution fee and slippage assumptions."""

    fixed_commission_per_contract: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate and normalize decimal inputs."""
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
        """Serialize cost assumptions for hashing and reporting."""
        return {
            "fixed_commission_per_contract": str(self.fixed_commission_per_contract),
            "slippage_bps": str(self.slippage_bps),
        }

    @property
    def slippage_model(self) -> str:
        """Describe whether slippage is modeled."""
        return "zero" if self.slippage_bps == Decimal("0") else "basis_points"

    @property
    def commission_model(self) -> str:
        """Describe commission handling for reports."""
        if self.fixed_commission_per_contract == Decimal("0"):
            return "zero"
        return "fixed_per_contract"


@dataclass(frozen=True, slots=True)
class BacktestEngineConfig:
    """Stable run-level inputs for constructing a backtest engine."""

    initial_cash: Decimal
    warmup_bars: int = 0
    target_timeframe: str | None = None
    strategy_version: str = ""
    config_payload: dict[str, Any] = field(default_factory=dict)
    dataset_metadata: tuple[DatasetMetadata, ...] = ()
    cost_model: BacktestCostModel = field(default_factory=BacktestCostModel)

    def __post_init__(self) -> None:
        """Normalize and validate constructor inputs."""
        object.__setattr__(self, "initial_cash", Decimal(str(self.initial_cash)))
        if self.initial_cash <= Decimal("0"):
            raise ValueError("initial_cash must be positive")
        if self.warmup_bars < 0:
            raise ValueError("warmup_bars must be non-negative")
        if self.target_timeframe is not None and not self.target_timeframe.strip():
            raise ValueError("target_timeframe, if set, must not be empty")
        object.__setattr__(self, "dataset_metadata", tuple(self.dataset_metadata))
        object.__setattr__(self, "config_payload", dict(self.config_payload))

    def to_payload(self) -> dict[str, Any]:
        """Serialize this engine config for stable hashing."""
        payload: dict[str, Any] = {
            "initial_cash": str(self.initial_cash),
            "warmup_bars": self.warmup_bars,
            "target_timeframe": self.target_timeframe,
            "strategy_version": self.strategy_version,
            "cost_model": self.cost_model.to_payload(),
        }
        if self.config_payload:
            payload["config"] = dict(self.config_payload)
        if self.dataset_metadata:
            payload["dataset_metadata"] = tuple(
                dataset_metadata_payload(item) for item in self.dataset_metadata
            )
        return payload


CostModelConfig = BacktestCostModel


@dataclass(frozen=True, slots=True)
class BacktestRiskConfig:
    """Backtest risk settings."""

    max_notional: Decimal
    schema_version: str = "1"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")
        object.__setattr__(self, "schema_version", self.schema_version.strip())
        object.__setattr__(self, "max_notional", Decimal(str(self.max_notional)))
        if self.max_notional <= Decimal("0"):
            raise ValueError("max_notional must be positive")

    def to_payload(self) -> dict[str, str]:
        """Perform to_payload."""
        return {
            "max_notional": str(self.max_notional),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class RollPolicyConfig:
    """Continuous futures roll policy for config-driven backtest runs."""

    enabled: bool = False
    method: str = "first_notice_date"
    roll_sessions_before_first_notice: int = 3

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        normalized = self.method.strip().lower()
        if normalized != "first_notice_date":
            raise ValueError("roll_policy.method must be first_notice_date")
        if self.roll_sessions_before_first_notice <= 0:
            raise ValueError("roll_sessions_before_first_notice must be positive")
        object.__setattr__(self, "method", normalized)

    def to_payload(self) -> dict[str, object]:
        """Perform to_payload."""
        return {
            "enabled": self.enabled,
            "method": self.method,
            "roll_sessions_before_first_notice": self.roll_sessions_before_first_notice,
        }


@dataclass(frozen=True, slots=True)
class BacktestMarketDataReference:
    """Run-level reference to a configured market data source."""

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


@dataclass(frozen=True, slots=True)
class BacktestStrategyConfig:
    """Configured strategy instance referenced by a backtest run."""

    class_path: str
    params: dict[str, Any] = field(default_factory=dict)
    strategy_id: str | None = None
    account_id: str | None = None
    allocation: Decimal = Decimal("1")
    enabled: bool = True
    signal_aggregation_policy: str = SignalAggregationPolicy.SUM_TARGETS.value
    signal_priority: int = 0
    signal_weight: Decimal = Decimal("1")
    conflict_group: str = "default"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.class_path.strip():
            raise ValueError("strategy class_path must not be empty")
        object.__setattr__(self, "params", dict(self.params))
        object.__setattr__(self, "allocation", Decimal(str(self.allocation)))
        object.__setattr__(self, "signal_weight", Decimal(str(self.signal_weight)))
        object.__setattr__(
            self,
            "signal_aggregation_policy",
            SignalAggregationPolicy(self.signal_aggregation_policy).value,
        )
        if self.strategy_id is not None and not self.strategy_id.strip():
            raise ValueError("strategy_id must not be empty")
        if self.account_id is not None and not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if self.allocation < Decimal("0"):
            raise ValueError("strategy allocation must be non-negative")
        if self.signal_weight < Decimal("0"):
            raise ValueError("strategy signal_weight must be non-negative")
        if self.signal_priority < 0:
            raise ValueError("strategy signal_priority must be non-negative")
        if not self.conflict_group.strip():
            raise ValueError("strategy conflict_group must not be empty")

    @classmethod
    def from_yaml(cls, path: Path) -> BacktestStrategyConfig:
        """Perform from_yaml."""
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("strategy config must be a mapping")
        return cls.from_payload(payload)

    def to_payload(self) -> dict[str, Any]:
        """Perform to_payload."""
        return {
            "strategy_id": self.strategy_id,
            "class_path": self.class_path,
            "account_id": self.account_id,
            "allocation": str(self.allocation),
            "enabled": self.enabled,
            "signal_aggregation_policy": self.signal_aggregation_policy,
            "signal_priority": self.signal_priority,
            "signal_weight": str(self.signal_weight),
            "conflict_group": self.conflict_group,
            "params": self.params,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> BacktestStrategyConfig:
        """Build a strategy config from a validated mapping payload."""
        return cls._parse_payload(dict(payload))

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
            signal_aggregation_policy=str(
                payload.get("signal_aggregation_policy", SignalAggregationPolicy.SUM_TARGETS.value)
            ),
            signal_priority=int(payload.get("signal_priority", 0)),
            signal_weight=Decimal(str(payload.get("signal_weight", "1"))),
            conflict_group=str(payload.get("conflict_group", "default")),
            params=params,
        )


@dataclass(frozen=True, slots=True)
class BacktestRuntimeConfig:
    """Complete identity for one backtest run.

    Historical stores, catalogs, chains, and CSV schemas belong to
    HistoricalMarketDataConfig; this config only references the chosen source.
    """

    roots: tuple[str, ...]
    symbols: tuple[str, ...]
    start: datetime
    end: datetime
    timeframe: str
    initial_cash: Decimal
    strategy_class: str = ""
    market_data: BacktestMarketDataReference = field(default_factory=BacktestMarketDataReference)
    strategy_config_path: Path | None = None
    strategy: BacktestStrategyConfig | None = None
    strategies: tuple[BacktestStrategyConfig, ...] = ()
    strategy_params: dict[str, Any] = field(default_factory=dict)
    instrument_ids: dict[str, InstrumentId] = field(default_factory=dict)
    cost_model: BacktestCostModel = field(default_factory=BacktestCostModel)
    risk_config: BacktestRiskConfig = field(
        default_factory=lambda: BacktestRiskConfig(max_notional=Decimal("1"))
    )
    roll_policy: RollPolicyConfig = field(default_factory=RollPolicyConfig)
    warmup_bars: int = 0
    mode: RuntimeMode | str = RuntimeMode.BACKTEST
    execution_environment: ExecutionEnvironment | str = ExecutionEnvironment.SIMULATED
    market_data_environment: MarketDataEnvironment | str = MarketDataEnvironment.REPLAY
    schema_version: str = "1"
    brokerage_model: str = "CUSTOM"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")
        object.__setattr__(self, "schema_version", self.schema_version.strip())
        mode = RuntimeMode.from_value(self.mode)
        if mode is not RuntimeMode.BACKTEST:
            raise ValueError("BacktestRuntimeConfig mode must be backtest")
        object.__setattr__(self, "mode", mode)
        execution_environment = ExecutionEnvironment.from_value(
            self.execution_environment,
            mode=mode,
        )
        if execution_environment is not ExecutionEnvironment.SIMULATED:
            raise ValueError("BacktestRuntimeConfig execution_environment must be simulated")
        object.__setattr__(self, "execution_environment", execution_environment)
        market_data_environment = MarketDataEnvironment.from_value(
            self.market_data_environment,
            mode=mode,
        )
        if market_data_environment is not MarketDataEnvironment.REPLAY:
            raise ValueError("BacktestRuntimeConfig market_data_environment must be replay")
        object.__setattr__(self, "market_data_environment", market_data_environment)
        if self.strategy_config_path is not None:
            object.__setattr__(self, "strategy_config_path", Path(self.strategy_config_path))
        if not isinstance(self.market_data, BacktestMarketDataReference):
            object.__setattr__(
                self,
                "market_data",
                BacktestMarketDataReference(**self.market_data),
            )
        if self.strategy is not None and not isinstance(self.strategy, BacktestStrategyConfig):
            object.__setattr__(self, "strategy", BacktestStrategyConfig(**self.strategy))
        object.__setattr__(
            self,
            "strategies",
            tuple(
                strategy
                if isinstance(strategy, BacktestStrategyConfig)
                else BacktestStrategyConfig(**strategy)
                for strategy in self.strategies
            ),
        )
        object.__setattr__(self, "roots", tuple(self.roots))
        object.__setattr__(self, "symbols", tuple(self.symbols))
        object.__setattr__(self, "initial_cash", Decimal(str(self.initial_cash)))
        object.__setattr__(self, "strategy_params", dict(self.strategy_params))
        if self.strategy is not None and self.strategies:
            raise ValueError("provide either strategy or strategies, not both")
        if self.strategy is not None:
            object.__setattr__(self, "strategy_class", self.strategy.class_path)
            object.__setattr__(self, "strategy_params", dict(self.strategy.params))
        if self.strategies:
            first_strategy = self.strategies[0]
            object.__setattr__(self, "strategy_class", first_strategy.class_path)
            object.__setattr__(self, "strategy_params", dict(first_strategy.params))
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
        if not self.market_data.is_configured:
            raise ValueError("market_data must be configured")
        brokerage_model = self.brokerage_model.strip().upper()
        if not brokerage_model:
            raise ValueError("brokerage_model must not be empty")
        object.__setattr__(self, "brokerage_model", brokerage_model)

    @classmethod
    def from_yaml(cls, path: Path) -> BacktestRuntimeConfig:
        """Perform from_yaml."""
        from qts.runtime.config_loader import BacktestConfigLoader

        return BacktestConfigLoader.from_path(path)

    @property
    def config_hash(self) -> str:
        """Perform config_hash."""
        return stable_json_hash(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        """Perform to_payload."""
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "mode": RuntimeMode.from_value(self.mode).value,
            "execution_environment": ExecutionEnvironment.from_value(
                self.execution_environment,
                mode=RuntimeMode.BACKTEST,
            ).value,
            "market_data_environment": MarketDataEnvironment.from_value(
                self.market_data_environment,
                mode=RuntimeMode.BACKTEST,
            ).value,
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
            "brokerage_model": self.brokerage_model,
        }
        market_data = self.market_data.to_payload()
        if market_data is not None:
            payload["market_data"] = market_data
        if self.strategy_config_path is not None:
            payload["strategy_config"] = str(self.strategy_config_path)
        if self.strategy is not None:
            payload["strategy"] = self.strategy.to_payload()
        if self.strategies:
            payload["strategies"] = [strategy.to_payload() for strategy in self.strategies]
        return payload

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Perform _normalize_symbol."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("instrument_ids must not contain empty symbols")
        return normalized


@dataclass(frozen=True, slots=True)
class BrokerRuntimeConfig:
    """Startup and safety configuration for broker-capable runtime modes."""

    _supported_modes: ClassVar[frozenset[RuntimeMode]] = frozenset(
        {
            RuntimeMode.PAPER_BROKER,
            RuntimeMode.LIVE_OBSERVATION,
            RuntimeMode.LIVE,
            RuntimeMode.OBSERVATION,
        }
    )

    mode: RuntimeMode | str
    broker_configured: bool
    account_configured: bool
    risk_configured: bool
    calendar_configured: bool
    kill_switch_configured: bool
    allow_live_orders: bool = False
    observation_only: bool = False
    broker_account_kind: str | None = None
    execution_environment: ExecutionEnvironment | str | None = None
    market_data_environment: MarketDataEnvironment | str | None = None
    account_environment: AccountEnvironment | str | None = None
    broker_account_code: str | None = None
    broker_port: int | None = None
    broker_port_override_reason: str | None = None
    operator_signoff_id: str | None = None
    api_read_only: bool = False
    broker_time_synced: bool = True
    market_data_permission_live: bool = True
    reconciliation_passed: bool = True
    open_order_reconciliation_passed: bool | None = None
    position_reconciliation_passed: bool | None = None
    cash_reconciliation_passed: bool | None = None
    event_sink_writable: bool = True
    snapshot_store_configured: bool = True
    schema_version: str = "1"

    def __post_init__(self) -> None:
        """Validate the broker runtime mode contract."""
        if not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")
        object.__setattr__(self, "schema_version", self.schema_version.strip())
        mode = RuntimeMode.from_value(self.mode)
        if mode is RuntimeMode.BACKTEST:
            raise ValueError("BrokerRuntimeConfig mode cannot be backtest")
        if mode not in self._supported_modes:
            raise ValueError(f"{self.__class__.__name__} mode cannot be {mode.value}")
        object.__setattr__(self, "mode", mode)
        execution_environment = ExecutionEnvironment.from_value(
            self.execution_environment,
            mode=mode,
        )
        market_data_environment = MarketDataEnvironment.from_value(
            self.market_data_environment,
            mode=mode,
        )
        account_environment = AccountEnvironment.from_value(self.account_environment, mode=mode)
        broker_account_kind = self._normalize_broker_account_kind(
            self.broker_account_kind,
            account_environment=account_environment,
        )
        object.__setattr__(self, "execution_environment", execution_environment)
        object.__setattr__(self, "market_data_environment", market_data_environment)
        object.__setattr__(self, "account_environment", account_environment)
        object.__setattr__(self, "broker_account_kind", broker_account_kind)
        if self.broker_account_code is not None:
            object.__setattr__(self, "broker_account_code", self.broker_account_code.strip())
        if self.operator_signoff_id is not None:
            object.__setattr__(self, "operator_signoff_id", self.operator_signoff_id.strip())
        if self.broker_port_override_reason is not None:
            object.__setattr__(
                self,
                "broker_port_override_reason",
                self.broker_port_override_reason.strip(),
            )
        if self.broker_port is None:
            if mode is RuntimeMode.LIVE:
                object.__setattr__(self, "broker_port", 4001)
            elif mode is RuntimeMode.PAPER_BROKER:
                object.__setattr__(self, "broker_port", 4002)
        if self.open_order_reconciliation_passed is None:
            object.__setattr__(
                self,
                "open_order_reconciliation_passed",
                self.reconciliation_passed,
            )
        if self.position_reconciliation_passed is None:
            object.__setattr__(
                self,
                "position_reconciliation_passed",
                self.reconciliation_passed,
            )
        if self.cash_reconciliation_passed is None:
            object.__setattr__(
                self,
                "cash_reconciliation_passed",
                self.reconciliation_passed,
            )
        self._validate_mode_contract(mode)

    @property
    def config_hash(self) -> str:
        """Return the stable identity hash for this broker runtime config."""
        return stable_json_hash(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        """Serialize startup gates and environment identity for evidence artifacts."""
        mode = RuntimeMode.from_value(self.mode)
        execution_environment = ExecutionEnvironment.from_value(
            self.execution_environment,
            mode=mode,
        )
        market_data_environment = MarketDataEnvironment.from_value(
            self.market_data_environment,
            mode=mode,
        )
        account_environment = AccountEnvironment.from_value(
            self.account_environment,
            mode=mode,
        )
        return {
            "schema_version": self.schema_version,
            "mode": mode.value,
            "broker_configured": self.broker_configured,
            "account_configured": self.account_configured,
            "risk_configured": self.risk_configured,
            "calendar_configured": self.calendar_configured,
            "kill_switch_configured": self.kill_switch_configured,
            "allow_live_orders": self.allow_live_orders,
            "observation_only": self.observation_only,
            "broker_account_kind": self.broker_account_kind,
            "execution_environment": execution_environment.value,
            "market_data_environment": market_data_environment.value,
            "account_environment": account_environment.value,
            "broker_account_code": self.broker_account_code,
            "broker_port": self.broker_port,
            "broker_port_override_reason": self.broker_port_override_reason,
            "operator_signoff_id": self.operator_signoff_id,
            "api_read_only": self.api_read_only,
            "broker_time_synced": self.broker_time_synced,
            "market_data_permission_live": self.market_data_permission_live,
            "reconciliation_passed": self.reconciliation_passed,
            "open_order_reconciliation_passed": self.open_order_reconciliation_passed,
            "position_reconciliation_passed": self.position_reconciliation_passed,
            "cash_reconciliation_passed": self.cash_reconciliation_passed,
            "event_sink_writable": self.event_sink_writable,
            "snapshot_store_configured": self.snapshot_store_configured,
        }

    @staticmethod
    def _normalize_broker_account_kind(
        value: str | None, *, account_environment: AccountEnvironment
    ) -> str:
        """Normalize the broker account classification for manifests."""
        if value is None:
            return account_environment.value
        normalized = value.strip().lower()
        if normalized not in {"paper", "live", "simulated"}:
            raise ValueError("broker_account_kind must be paper, live, or simulated")
        return normalized

    def _validate_mode_contract(self, mode: RuntimeMode) -> None:
        """Validate mode, account, execution, and port consistency."""
        is_paper_account = self.broker_account_kind == "paper"
        is_live_account = self.broker_account_kind == "live"
        if mode is RuntimeMode.LIVE:
            if is_paper_account:
                raise ValueError("live mode cannot use a paper account")
            if self.broker_account_code and not is_live_account:
                raise ValueError("live mode requires a live account")
            if self.broker_account_kind != AccountEnvironment.LIVE.value:
                raise ValueError("live mode requires broker_account_kind=live")
            if self.account_environment is not AccountEnvironment.LIVE:
                raise ValueError("live mode requires account_environment=live")
            if self.execution_environment is not ExecutionEnvironment.BROKER:
                raise ValueError("live mode requires execution_environment=broker")
            if self.market_data_environment is not MarketDataEnvironment.REALTIME:
                raise ValueError("live mode requires market_data_environment=realtime")
            if self.broker_port is not None and self.broker_port != 4001:
                if not self.broker_port_override_reason:
                    raise ValueError(
                        "live broker port override requires broker_port_override_reason"
                    )
            if not self.allow_live_orders:
                raise ValueError("live mode requires allow_live_orders=true")
            if not self.operator_signoff_id:
                raise ValueError("live mode requires operator_signoff_id")
            if self.observation_only:
                raise ValueError("live mode with allow_live_orders cannot be observation_only")
            return

        if self.allow_live_orders:
            raise ValueError(f"{mode.value} mode cannot allow live orders")

        if mode is RuntimeMode.PAPER_BROKER:
            if self.broker_account_code and not is_paper_account:
                raise ValueError("paper broker mode requires a paper account")
            if self.broker_account_kind != AccountEnvironment.PAPER.value:
                raise ValueError("paper broker mode requires broker_account_kind=paper")
            if self.execution_environment is not ExecutionEnvironment.BROKER:
                raise ValueError("paper broker mode requires execution_environment=broker")
            if self.broker_port is not None and self.broker_port != 4002:
                raise ValueError("paper broker mode requires broker port 4002")
            return

        if mode is RuntimeMode.PAPER_SIMULATED:
            if self.execution_environment is not ExecutionEnvironment.SIMULATED:
                raise ValueError("paper simulated mode requires execution_environment=simulated")
            if self.account_environment is not AccountEnvironment.SIMULATED:
                raise ValueError("paper simulated mode requires account_environment=simulated")
            if self.broker_account_kind != AccountEnvironment.SIMULATED.value:
                raise ValueError("paper simulated mode requires broker_account_kind=simulated")
            return

        if mode in {RuntimeMode.OBSERVATION, RuntimeMode.LIVE_OBSERVATION}:
            object.__setattr__(self, "observation_only", True)
            if self.execution_environment is not ExecutionEnvironment.DISABLED:
                raise ValueError(f"{mode.value} mode requires execution_environment=disabled")


__all__ = [
    "TradingRuntimeConfig",
    "ConfigMigration",
    "ConfigMigrationResult",
    "BacktestMarketDataReference",
    "BacktestRuntimeConfig",
    "BrokerRuntimeConfig",
    "BacktestEngineConfig",
    "BacktestCostModel",
    "BacktestStrategyConfig",
    "CostModelConfig",
    "BacktestRiskConfig",
    "RollPolicyConfig",
]
