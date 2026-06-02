"""Final-readiness gate for multi-account runtime/backtest coverage."""

from __future__ import annotations

from pathlib import Path


def test_final_readiness_includes_multi_account_runtime_and_backtest_gates() -> None:
    required_tests = {
        Path("tests/unit/backtest/test_backtest_actor_loop.py"): (
            "test_backtest_actor_loop_routes_multi_account_strategies_to_account_partitions"
        ),
        Path("tests/unit/runtime/test_runtime_session.py"): (
            "test_runtime_session_routes_intents_to_multi_account_topology_partitions"
        ),
        Path("tests/integration/test_live_kill_switch_flow.py"): (
            "test_live_kill_switch_with_multi_account_topology_cancels_all_active_orders"
        ),
    }

    missing: list[str] = []
    for path, test_name in required_tests.items():
        text = path.read_text(encoding="utf-8")
        if f"def {test_name}" not in text:
            missing.append(f"{path}:{test_name}")

    assert missing == []
