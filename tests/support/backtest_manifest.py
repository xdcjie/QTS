from __future__ import annotations

from typing import Any


def m1_manifest_kwargs() -> dict[str, Any]:
    """Return complete M1 backtest manifest fields for direct writer tests."""
    return {
        "dataset_metadata": (
            {
                "dataset_id": "test-dataset",
                "file_hash": "sha256:test-dataset",
                "row_count": 1,
                "first_ts": "2026-01-02T14:30:00+00:00",
                "last_ts": "2026-01-02T14:31:00+00:00",
                "timezone": "UTC",
                "adjustment_mode": "raw",
            },
        ),
        "runtime_topology_payload": {"topology_hash": "sha256:test-topology"},
        "risk_config_hash": "sha256:test-risk",
        "execution_assumptions": {
            "fill_model_name": "immediate_market_fill",
            "fill_model_version": "1",
            "slippage_model": "zero",
            "commission_model": "zero",
            "partial_fill_policy": "none",
            "broker_capability_model": {"broker_id": "test-simulated"},
        },
    }
