"""IBKR runtime configuration guardrails."""

from __future__ import annotations

from collections.abc import Mapping, Set
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]

IbkrMode = Literal["paper", "live"]
IbkrTransport = Literal["official", "async"]
IBKR_PAPER_GATEWAY_PORT = 4002


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
    transport: IbkrTransport = "official"
    observe_only: bool = False

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

        transport_value = str(payload.get("transport", "official")).strip()
        if transport_value == "official":
            transport: IbkrTransport = "official"
        elif transport_value == "async":
            transport = "async"
        else:
            raise ValueError("transport must be official or async")

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
            transport=transport,
            observe_only=cls._read_bool(payload, "observe_only", default=False),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> IbkrEnvironmentConfig:
        """Load and validate environment config from YAML file."""

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"{path} must contain a YAML mapping")
        return cls.from_payload(payload)

    @staticmethod
    def _read_bool(payload: Mapping[str, Any], key: str, *, default: bool) -> bool:
        value = payload.get(key, default)
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be a boolean")
        return value

    def uses_paper_gateway_port(self) -> bool:
        """Return whether any configured boundary points at the paper Gateway port."""

        return (
            self.market_data.port == IBKR_PAPER_GATEWAY_PORT
            or self.order_execution.port == IBKR_PAPER_GATEWAY_PORT
        )

    def account_classification(self) -> str:
        """Classify the configured account without exposing credential values."""

        account_id = self.order_execution.account_id
        if is_ibkr_paper_account(account_id):
            return "paper"
        if is_ibkr_live_account(account_id):
            return "live"
        return "unknown"


def is_ibkr_paper_account(account_id: str) -> bool:
    """Return whether an IBKR account code identifies a paper account."""

    return account_id.strip().upper().startswith("DUP")


def is_ibkr_live_account(account_id: str) -> bool:
    """Return whether an IBKR account code identifies a live account."""

    normalized = account_id.strip().upper()
    return normalized.startswith("DU") and not normalized.startswith("DUP")


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

    if config.mode == "paper" and not is_ibkr_paper_account(config.order_execution.account_id):
        errors.append("paper mode requires a paper account")

    if config.mode == "live":
        paper_client_ids = paper_client_ids or set()
        if is_ibkr_paper_account(config.order_execution.account_id):
            errors.append("live mode cannot use a paper account")
        elif not is_ibkr_live_account(config.order_execution.account_id):
            errors.append("live mode requires a live account")
        if config.uses_paper_gateway_port() and not config.observe_only:
            errors.append(
                "live mode cannot use paper Gateway port 4002 unless observe_only is true"
            )
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
    "IBKR_PAPER_GATEWAY_PORT",
    "IbkrConnectionConfig",
    "collect_validation_errors",
    "IbkrEnvironmentConfig",
    "IbkrMode",
    "IbkrOrderExecutionConfig",
    "IbkrSecretRefs",
    "IbkrTransport",
    "validate_ibkr_environment",
]
