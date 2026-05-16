from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]


def test_ibkr_paper_config_separates_market_data_and_order_execution() -> None:
    config = yaml.safe_load(Path("configs/paper.ibkr.example.yaml").read_text())

    assert config["mode"] == "paper"
    assert config["provider"] == "ibkr"
    assert config["transport"] == "official"
    assert set(config["connections"]) == {"market_data", "order_execution"}
    assert (
        config["connections"]["market_data"]["client_id"]
        != config["connections"]["order_execution"]["client_id"]
    )
    assert config["order_execution"]["account_id"].startswith("DUP")


def test_ibkr_live_config_separates_market_data_and_order_execution() -> None:
    config = yaml.safe_load(Path("configs/live.ibkr.example.yaml").read_text())

    assert config["mode"] == "live"
    assert config["provider"] == "ibkr"
    assert config["transport"] == "official"
    assert set(config["connections"]) == {"market_data", "order_execution"}
    assert (
        config["connections"]["market_data"]["client_id"]
        != config["connections"]["order_execution"]["client_id"]
    )
    assert config["order_execution"]["account_id"].startswith("DU")
    assert not config["order_execution"]["account_id"].startswith("DUP")
