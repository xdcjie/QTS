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
