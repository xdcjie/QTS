from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_ibkr_gateway_paper_readiness_requires_complete_evidence(
    request: pytest.FixtureRequest,
) -> None:
    evidence_dir_option = request.config.getoption("--evidence-dir")
    if evidence_dir_option is None:
        pytest.skip("--evidence-dir is required to validate paper readiness evidence")
    evidence_dir = Path(str(evidence_dir_option))
    if not evidence_dir.exists():
        pytest.skip(f"paper readiness evidence directory does not exist: {evidence_dir}")

    required = {
        "observe_only": False,
        "market_data": False,
        "non_marketable_cancel": False,
        "tiny_paper_fill": False,
        "strategy_order": False,
        "reconciliation_clean": False,
        "submitted_via_runtime_session": False,
        "account_config_matches_gateway": False,
    }
    for path in evidence_dir.glob("paper-full-chain-*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in required:
            required[key] = required[key] or bool(payload.get(key))

    missing = [key for key, present in required.items() if not present]
    assert missing == []
