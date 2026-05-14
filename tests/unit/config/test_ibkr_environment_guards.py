from __future__ import annotations

import pytest


def test_live_ibkr_config_rejects_paper_account_and_client_ids_without_leaking_secrets() -> None:
    from qts.config.ibkr import (
        IbkrConnectionConfig,
        IbkrEnvironmentConfig,
        IbkrOrderExecutionConfig,
        IbkrSecretRefs,
        validate_ibkr_environment,
    )

    config = IbkrEnvironmentConfig(
        mode="live",
        market_data=IbkrConnectionConfig(
            host="127.0.0.1",
            port=7496,
            client_id=101,
        ),
        order_execution=IbkrOrderExecutionConfig(
            host="127.0.0.1",
            port=7496,
            client_id=201,
            account_id="DU1234567",
            risk_profile="paper-default",
        ),
        secrets=IbkrSecretRefs(
            username_env="IBKR_PAPER_USERNAME",
            password_env="supersecret-password",
        ),
    )

    with pytest.raises(ValueError) as excinfo:
        validate_ibkr_environment(config, paper_client_ids={101, 201})

    message = str(excinfo.value)
    assert "paper account" in message
    assert "paper client_id" in message
    assert "paper secret reference" in message
    assert "paper risk profile" in message
    assert "supersecret-password" not in message


def test_valid_live_ibkr_config_requires_distinct_market_data_and_order_clients() -> None:
    from qts.config.ibkr import (
        IbkrConnectionConfig,
        IbkrEnvironmentConfig,
        IbkrOrderExecutionConfig,
        IbkrSecretRefs,
        validate_ibkr_environment,
    )

    config = IbkrEnvironmentConfig(
        mode="live",
        market_data=IbkrConnectionConfig(
            host="127.0.0.1",
            port=7496,
            client_id=111,
        ),
        order_execution=IbkrOrderExecutionConfig(
            host="127.0.0.1",
            port=7496,
            client_id=211,
            account_id="U1234567",
            risk_profile="live-default",
        ),
        secrets=IbkrSecretRefs(
            username_env="IBKR_LIVE_USERNAME",
            password_env="IBKR_LIVE_PASSWORD",
        ),
    )

    validate_ibkr_environment(config, paper_client_ids={101, 201})


def test_ibkr_config_rejects_shared_market_data_and_order_client_id() -> None:
    from qts.config.ibkr import (
        IbkrConnectionConfig,
        IbkrEnvironmentConfig,
        IbkrOrderExecutionConfig,
        IbkrSecretRefs,
        validate_ibkr_environment,
    )

    config = IbkrEnvironmentConfig(
        mode="paper",
        market_data=IbkrConnectionConfig(
            host="127.0.0.1",
            port=7497,
            client_id=101,
        ),
        order_execution=IbkrOrderExecutionConfig(
            host="127.0.0.1",
            port=7497,
            client_id=101,
            account_id="DU1234567",
            risk_profile="paper-default",
        ),
        secrets=IbkrSecretRefs(
            username_env="IBKR_PAPER_USERNAME",
            password_env="IBKR_PAPER_PASSWORD",
        ),
    )

    with pytest.raises(ValueError, match="market data and order execution client_id"):
        validate_ibkr_environment(config)


def test_paper_ibkr_config_accepts_local_paper_gateway_on_distinct_clients() -> None:
    from qts.config.ibkr import (
        IbkrConnectionConfig,
        IbkrEnvironmentConfig,
        IbkrOrderExecutionConfig,
        IbkrSecretRefs,
        validate_ibkr_environment,
    )

    config = IbkrEnvironmentConfig(
        mode="paper",
        observe_only=True,
        market_data=IbkrConnectionConfig(
            host="127.0.0.1",
            port=4002,
            client_id=101,
        ),
        order_execution=IbkrOrderExecutionConfig(
            host="127.0.0.1",
            port=4002,
            client_id=201,
            account_id="DU1234567",
            risk_profile="paper-default",
        ),
        secrets=IbkrSecretRefs(
            username_env="IBKR_PAPER_USERNAME",
            password_env="IBKR_PAPER_PASSWORD",
        ),
    )

    validate_ibkr_environment(config)


def test_live_ibkr_config_rejects_paper_gateway_port_unless_observe_only() -> None:
    from qts.config.ibkr import (
        IbkrConnectionConfig,
        IbkrEnvironmentConfig,
        IbkrOrderExecutionConfig,
        IbkrSecretRefs,
        validate_ibkr_environment,
    )

    config = IbkrEnvironmentConfig(
        mode="live",
        market_data=IbkrConnectionConfig(
            host="127.0.0.1",
            port=4002,
            client_id=111,
        ),
        order_execution=IbkrOrderExecutionConfig(
            host="127.0.0.1",
            port=4002,
            client_id=211,
            account_id="U1234567",
            risk_profile="live-default",
        ),
        secrets=IbkrSecretRefs(
            username_env="IBKR_LIVE_USERNAME",
            password_env="IBKR_LIVE_PASSWORD",
        ),
    )

    with pytest.raises(ValueError, match="paper Gateway port 4002"):
        validate_ibkr_environment(config)

    observation_config = IbkrEnvironmentConfig(
        mode="live",
        observe_only=True,
        market_data=config.market_data,
        order_execution=config.order_execution,
        secrets=config.secrets,
    )

    validate_ibkr_environment(observation_config)


def test_ibkr_environment_config_reads_transport_with_official_default() -> None:
    from qts.config.ibkr import IbkrEnvironmentConfig

    payload = {
        "mode": "paper",
        "provider": "ibkr",
        "connections": {
            "market_data": {"host": "127.0.0.1", "port": 4002, "client_id": 101},
            "order_execution": {"host": "127.0.0.1", "port": 4002, "client_id": 201},
        },
        "order_execution": {"account_id": "DU1234567", "risk_profile": "paper-default"},
        "secrets": {
            "username_env": "IBKR_PAPER_USERNAME",
            "password_env": "IBKR_PAPER_PASSWORD",
        },
    }

    default_config = IbkrEnvironmentConfig.from_payload(payload)
    async_config = IbkrEnvironmentConfig.from_payload({**payload, "transport": "async"})

    assert default_config.transport == "official"
    assert async_config.transport == "async"


def test_ibkr_environment_config_rejects_unknown_transport() -> None:
    from qts.config.ibkr import IbkrEnvironmentConfig

    payload = {
        "mode": "paper",
        "provider": "ibkr",
        "transport": "ib-insync",
        "connections": {
            "market_data": {"host": "127.0.0.1", "port": 4002, "client_id": 101},
            "order_execution": {"host": "127.0.0.1", "port": 4002, "client_id": 201},
        },
        "order_execution": {"account_id": "DU1234567", "risk_profile": "paper-default"},
        "secrets": {
            "username_env": "IBKR_PAPER_USERNAME",
            "password_env": "IBKR_PAPER_PASSWORD",
        },
    }

    with pytest.raises(ValueError, match="transport must be official or async"):
        IbkrEnvironmentConfig.from_payload(payload)
