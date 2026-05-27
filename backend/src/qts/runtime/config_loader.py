"""Load and parse backtest configuration files."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from qts.core.ids import InstrumentId
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
    BacktestStrategyConfig,
    BacktestCostModel,
    RollPolicyConfig,
)


class BacktestConfigLoader:
    """Load backtest configuration from YAML or payload dictionaries."""

    @classmethod
    def from_path(cls, path: Path) -> BacktestRuntimeConfig:
        """Perform from_path."""
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("backtest config must be a mapping")
        return cls.from_payload(payload)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> BacktestRuntimeConfig:
        """Perform from_payload."""
        if "historical_data" in payload:
            raise ValueError("backtest run configs must use market_data")
        if "dataset_root" in payload:
            raise ValueError("backtest run configs must use market_data")
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

        strategy_config_path = (
            Path(str(payload["strategy_config"]))
            if payload.get("strategy_config") is not None
            else None
        )

        raw_strategies = payload.get("strategies")
        strategies: tuple[BacktestStrategyConfig, ...] = ()
        if raw_strategies is not None:
            if not isinstance(raw_strategies, list | tuple) or not raw_strategies:
                raise ValueError("strategies must be a non-empty list")
            parsed_strategies: list[BacktestStrategyConfig] = []
            for index, raw_strategy in enumerate(raw_strategies):
                if not isinstance(raw_strategy, dict):
                    raise ValueError(f"strategies[{index}] must be a mapping")
                parsed_strategies.append(BacktestStrategyConfig.from_payload(raw_strategy))
            strategies = tuple(parsed_strategies)

        strategy = None
        strategy_class: str
        if strategies:
            if (
                strategy_config_path is not None
                or "strategy_class" in payload
                or "strategy_params" in payload
            ):
                raise ValueError(
                    "strategies must not be combined with strategy_config, "
                    "strategy_class, or strategy_params"
                )
            strategy_class = strategies[0].class_path
            strategy_params = dict(strategies[0].params)
        elif strategy_config_path is not None:
            if "strategy_class" in payload or "strategy_params" in payload:
                raise ValueError(
                    "strategy_config must not be combined with strategy_class or strategy_params"
                )
            strategy = BacktestStrategyConfig.from_yaml(strategy_config_path)
            strategy_class = strategy.class_path
            strategy_params = dict(strategy.params)
        else:
            strategy_class = str(payload["strategy_class"])

        return BacktestRuntimeConfig(
            roots=tuple(payload["roots"]),
            symbols=tuple(payload["symbols"]),
            start=cls._parse_datetime(str(payload["start"])),
            end=cls._parse_datetime(str(payload["end"])),
            timeframe=payload["timeframe"],
            initial_cash=Decimal(str(payload["initial_cash"])),
            strategy_class=strategy_class,
            market_data=cls._parse_market_data_reference(payload.get("market_data")),
            strategy_config_path=strategy_config_path,
            strategy=strategy,
            strategies=strategies,
            strategy_params=cast(dict[str, Any], strategy_params),
            instrument_ids={
                str(symbol): InstrumentId(str(instrument_id))
                for symbol, instrument_id in instrument_ids_payload.items()
            },
            cost_model=BacktestCostModel(
                fixed_commission_per_contract=Decimal(
                    str(cost_payload.get("fixed_commission_per_contract", "0"))
                ),
                slippage_bps=Decimal(str(cost_payload.get("slippage_bps", "0"))),
            ),
            risk_config=BacktestRiskConfig(
                max_notional=Decimal(str(risk_payload.get("max_notional", "1"))),
                schema_version=str(risk_payload.get("schema_version", "1")),
            ),
            roll_policy=RollPolicyConfig(
                enabled=bool(roll_payload.get("enabled", False)),
                method=str(roll_payload.get("method", "first_notice_date")),
                roll_sessions_before_first_notice=int(
                    roll_payload.get("roll_sessions_before_first_notice", 3)
                ),
            ),
            warmup_bars=int(payload.get("warmup_bars", 0)),
            schema_version=str(payload.get("schema_version", "1")),
        )

    @staticmethod
    def _parse_datetime(value: datetime | str) -> datetime:
        """Perform _parse_datetime."""
        if isinstance(value, datetime):
            parsed = value
        else:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("datetime values must be timezone-aware")
        return parsed.astimezone(UTC)

    @staticmethod
    def _parse_market_data_reference(payload: object) -> BacktestMarketDataReference:
        """Perform _parse_market_data_reference."""
        if payload is None:
            return BacktestMarketDataReference()
        if not isinstance(payload, dict):
            raise ValueError("market_data must be a mapping")
        return BacktestMarketDataReference(
            config_path=Path(str(payload["config"])),
            catalog=str(payload["catalog"]),
            source=str(payload.get("source", "local_historical")),
        )
