from __future__ import annotations

import pytest
from qts.runtime.live import LiveMode, LiveStartupConfig, validate_live_startup


def test_live_startup_guard_requires_all_safety_controls_for_live_mode() -> None:
    config = LiveStartupConfig(
        mode=LiveMode.LIVE,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=False,
    )

    with pytest.raises(ValueError, match="kill_switch_configured"):
        validate_live_startup(config)


def test_observation_mode_allows_connections_but_blocks_real_order_submission() -> None:
    config = LiveStartupConfig(
        mode=LiveMode.OBSERVATION,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert validate_live_startup(config).real_order_submission_enabled is False
