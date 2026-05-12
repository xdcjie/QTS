"""IBKR runtime configuration guardrails."""

from __future__ import annotations

from collections.abc import Mapping, Set
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]

IbkrMode = Literal["paper", "live"]


@dataclass(frozen=True, slots=True)
class IbkrConnectionConfig:
    """IBKR connection settings for one boundary."""

    host: str
    port: int
    client_id: int
    source_id: str | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if self.source_id is not None and not self.source_id.strip():
            raise ValueError("source_id must not be empty when provided")


@dataclass(frozen=True, slots=True)
class IbkrOrderExecutionConfig:
    """IBKR order execution settings."""

    host: str
    port: int
    client_id: int
    account_id: str
    risk_profile: str
    source_id: str | None = None
    broker_id: str | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")
        if self.source_id is not None and not self.source_id.strip():
            raise ValueError("source_id must not be empty when provided")
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if not self.risk_profile.strip():
            raise ValueError("risk_profile must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrSecretRefs:
    """Environment variable names for IBKR credentials."""

    username_env: str
    password_env: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.username_env.strip():
            raise ValueError("username_env must not be empty")
        if not self.password_env.strip():
            raise ValueError("password_env must not be empty")


@dataclass(frozen=True, slots=True)
class IbkrEnvironmentConfig:
    """IBKR runtime configuration split by external boundary."""

    mode: IbkrMode
    market_data: IbkrConnectionConfig
    order_execution: IbkrOrderExecutionConfig
    secrets: IbkrSecretRefs

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> IbkrEnvironmentConfig:
        """Build a typed config from a mapping payload."""

        if str(payload.get("provider", "").strip()) != "ibkr":
            raise ValueError("provider must be ibkr")

        mode_value = str(payload.get("mode", "")).strip()
        if mode_value == "paper":
            mode: IbkrMode = "paper"
        elif mode_value == "live":
            mode = "live"
        else:
            raise ValueError("mode must be paper or live")

        connections = _as_mapping(payload, "connections")
        market_data = _as_mapping(connections, "market_data")
        order_execution_connection = _as_mapping(connections, "order_execution")
        order_execution_payload = _as_mapping(payload, "order_execution")
        secrets = _as_mapping(payload, "secrets")

        return cls(
            mode=mode,
            market_data=_read_connection(market_data, "market_data"),
            order_execution=_read_order_execution_config(
                order_execution_connection, order_execution_payload
            ),
            secrets=_read_secret_refs(secrets),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> IbkrEnvironmentConfig:
        """Load and validate environment config from YAML file."""

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"{path} must contain a YAML mapping")
        return cls.from_payload(payload)


def collect_validation_errors(
    config: IbkrEnvironmentConfig, *, paper_client_ids: Set[int] | None = None
) -> list[str]:
    """Return validation errors for config without raising."""

    try:
        validate_ibkr_environment(config, paper_client_ids=paper_client_ids)
    except ValueError as exc:
        return [item for item in str(exc).split("; ") if item]
    return []


def validate_ibkr_environment(
    config: IbkrEnvironmentConfig,
    *,
    paper_client_ids: Set[int] | None = None,
) -> None:
    """Validate paper/live separation without exposing secret values."""

    errors: list[str] = []
    if config.market_data.client_id == config.order_execution.client_id:
        errors.append("market data and order execution client_id must be distinct")

    if config.mode == "live":
        paper_client_ids = paper_client_ids or set()
        if config.order_execution.account_id.upper().startswith("DU"):
            errors.append("live mode cannot use a paper account")
        live_client_ids = {
            config.market_data.client_id,
            config.order_execution.client_id,
        }
        if live_client_ids.intersection(paper_client_ids):
            errors.append("live mode cannot use a paper client_id")
        if _contains_paper_reference(config.secrets.username_env) or _contains_paper_reference(
            config.secrets.password_env
        ):
            errors.append("live mode cannot use a paper secret reference")
        if "paper" in config.order_execution.risk_profile.lower():
            errors.append("live mode cannot use a paper risk profile")

    if errors:
        raise ValueError("; ".join(errors))


def _as_mapping(payload: Any, path: str) -> Mapping[str, Any]:
    """Perform _as_mapping."""
    value: Any = payload
    for key in path.split("."):
        if not isinstance(value, Mapping):
            raise ValueError(f"{path} must be a mapping")
        if key not in value:
            raise ValueError(f"{path} must be a mapping")
        value = value[key]
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be a mapping")
    return value


def _read_connection(payload: Mapping[str, Any], path: str) -> IbkrConnectionConfig:
    """Perform _read_connection."""
    host = str(payload.get("host", ""))
    port = payload.get("port")
    client_id = payload.get("client_id")
    source_id = payload.get("source_id")

    if not isinstance(port, int):
        raise ValueError(f"{path}.port must be a positive integer")
    if not isinstance(client_id, int):
        raise ValueError(f"{path}.client_id must be a positive integer")

    return IbkrConnectionConfig(
        host=host,
        port=port,
        client_id=client_id,
        source_id=str(source_id) if source_id is not None else None,
    )


def _read_order_execution_config(
    connection: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> IbkrOrderExecutionConfig:
    """Perform _read_order_execution_config."""
    order_execution = _read_connection(connection, "order_execution")
    account_id = str(payload.get("account_id", ""))
    risk_profile = str(payload.get("risk_profile", ""))
    broker_id = payload.get("broker_id")

    return IbkrOrderExecutionConfig(
        host=order_execution.host,
        port=order_execution.port,
        client_id=order_execution.client_id,
        source_id=order_execution.source_id,
        account_id=account_id,
        risk_profile=risk_profile,
        broker_id=broker_id if broker_id is not None else None,
    )


def _read_secret_refs(payload: Mapping[str, Any]) -> IbkrSecretRefs:
    """Perform _read_secret_refs."""
    return IbkrSecretRefs(
        username_env=str(payload.get("username_env", "")),
        password_env=str(payload.get("password_env", "")),
    )


def _contains_paper_reference(secret_env_name: str) -> bool:
    """Perform _contains_paper_reference."""
    return "PAPER" in secret_env_name.upper()


__all__ = [
    "IbkrConnectionConfig",
    "collect_validation_errors",
    "IbkrEnvironmentConfig",
    "IbkrMode",
    "IbkrOrderExecutionConfig",
    "IbkrSecretRefs",
    "validate_ibkr_environment",
]
