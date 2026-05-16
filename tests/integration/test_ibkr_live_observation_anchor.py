from __future__ import annotations

from pathlib import Path

import pytest


def test_ibkr_live_observation_anchor_requires_observation_only_config(
    request: pytest.FixtureRequest,
) -> None:
    if not request.config.getoption("--live-observation-only"):
        pytest.skip("--live-observation-only is required for live observation anchors")
    config_option = request.config.getoption("--config")
    if config_option is None:
        pytest.fail("--config is required for live observation anchors")
    config_path = Path(str(config_option))
    if not config_path.exists():
        pytest.skip(f"live observation config does not exist: {config_path}")

    import yaml  # type: ignore[import-untyped]

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    account_id = str(payload.get("order_execution", {}).get("account_id", ""))
    mode = str(payload.get("mode", ""))
    orders_enabled = bool(payload.get("orders_enabled", False))

    assert mode == "live"
    assert account_id.upper().startswith("DU")
    assert not account_id.upper().startswith("DUP")
    assert orders_enabled is False
