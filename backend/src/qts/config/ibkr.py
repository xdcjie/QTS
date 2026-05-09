"""IBKR runtime configuration guardrails."""

from __future__ import annotations

from collections.abc import Set
from dataclasses import dataclass
from typing import Literal

IbkrMode = Literal["paper", "live"]


@dataclass(frozen=True, slots=True)
class IbkrConnectionConfig:
    """IBKR connection settings for one boundary."""

    host: str
    port: int
    client_id: int

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if self.client_id <= 0:
            raise ValueError("client_id must be positive")


@dataclass(frozen=True, slots=True)
class IbkrOrderExecutionConfig(IbkrConnectionConfig):
    """IBKR order execution settings."""

    account_id: str
    risk_profile: str

    def __post_init__(self) -> None:
        IbkrConnectionConfig.__post_init__(self)
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


def _contains_paper_reference(secret_env_name: str) -> bool:
    return "PAPER" in secret_env_name.upper()


__all__ = [
    "IbkrConnectionConfig",
    "IbkrEnvironmentConfig",
    "IbkrMode",
    "IbkrOrderExecutionConfig",
    "IbkrSecretRefs",
    "validate_ibkr_environment",
]
