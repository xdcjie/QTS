from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

EXTERNAL_SMOKES = (
    "paper_broker_gateway_market_data_anchor",
    "paper_broker_submit_cancel_drill",
)


pytestmark = [pytest.mark.anchor, pytest.mark.external]


def test_external_readiness_smoke_matrix_requires_ibkr_paper_evidence(
    request: pytest.FixtureRequest,
) -> None:
    if os.environ.get("QTS_RUN_EXTERNAL_READINESS_SMOKES") != "1":
        pytest.skip("external IBKR paper readiness smokes are excluded from local CI")
    evidence_dir_option = request.config.getoption("--evidence-dir")
    if evidence_dir_option is None:
        pytest.skip("--evidence-dir is required for external IBKR paper readiness smokes")

    evidence_dir = Path(str(evidence_dir_option))
    if not evidence_dir.exists():
        pytest.skip(f"external readiness evidence directory does not exist: {evidence_dir}")

    found: dict[str, bool] = {smoke_name: False for smoke_name in EXTERNAL_SMOKES}
    for path in evidence_dir.glob("readiness-smoke-*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        smoke_name = str(payload.get("smoke_name", ""))
        if smoke_name not in found:
            continue
        found[smoke_name] = _has_external_artifact_identity(payload)

    missing = [smoke_name for smoke_name, present in found.items() if not present]
    assert missing == [], f"missing external readiness smoke evidence: {missing}"


def _has_external_artifact_identity(payload: dict[str, object]) -> bool:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return False
    events = artifacts.get("events")
    if not isinstance(events, dict):
        return False
    run_id = payload.get("run_id")
    correlation_id = payload.get("correlation_id")
    return (
        isinstance(run_id, str)
        and bool(run_id.strip())
        and isinstance(correlation_id, str)
        and bool(correlation_id.strip())
        and bool(payload.get("manifest_path"))
        and bool(events.get("path"))
        and int(events.get("rows", 0)) > 0
    )
