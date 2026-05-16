from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.application.commands.external_readiness_smoke_evidence import (
    generate_external_readiness_smoke_evidence,
)


def test_generator_derives_external_smoke_files_from_full_chain_evidence(
    tmp_path: Path,
) -> None:
    evidence_dir = tmp_path / "evidence" / "ibkr"
    event_path = evidence_dir / "paper-full-chain-events-20260516T010203Z.ndjson"
    manifest_path = evidence_dir / "paper-runtime.manifest.json"
    full_chain_path = evidence_dir / "paper-full-chain-20260516T010203Z.json"
    evidence_dir.mkdir(parents=True)
    event_path.write_text(
        '{"sequence":1,"kind":"runtime.market_data","event_hash":"sha256:md"}\n'
        '{"sequence":2,"kind":"runtime.order_submitted","event_hash":"sha256:order"}\n',
        encoding="utf-8",
    )
    manifest_path.write_text('{"runtime_mode":"paper_broker"}\n', encoding="utf-8")
    full_chain_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2026-05-16T01:02:03+00:00",
                "gateway": "127.0.0.1:4002",
                "market_data": True,
                "non_marketable_cancel": True,
                "strategy_order": True,
                "submitted_via_runtime_session": True,
                "reconciliation_clean": True,
                "account_config_matches_gateway": True,
                "report_manifest": str(manifest_path),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    generated = generate_external_readiness_smoke_evidence(evidence_dir=evidence_dir)

    assert {path.name for path in generated} == {
        "readiness-smoke-paper_broker_gateway_market_data_anchor.json",
        "readiness-smoke-paper_broker_submit_cancel_drill.json",
    }
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in generated]
    assert {payload["smoke_name"] for payload in payloads} == {
        "paper_broker_gateway_market_data_anchor",
        "paper_broker_submit_cancel_drill",
    }
    for payload in payloads:
        assert payload["run_id"] == "ibkr-paper-full-chain-20260516T010203Z"
        assert payload["correlation_id"]
        assert payload["manifest_path"] == str(manifest_path)
        assert payload["artifacts"]["events"]["path"] == str(event_path)
        assert payload["artifacts"]["events"]["rows"] == 2
        assert payload["source_evidence_path"] == str(full_chain_path)


def test_generator_rejects_incomplete_full_chain_evidence(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence" / "ibkr"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "paper-full-chain-20260516T010203Z.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2026-05-16T01:02:03+00:00",
                "market_data": True,
                "non_marketable_cancel": False,
                "strategy_order": True,
                "submitted_via_runtime_session": True,
                "reconciliation_clean": True,
                "account_config_matches_gateway": True,
                "report_manifest": "missing.manifest.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="no complete paper full-chain evidence"):
        generate_external_readiness_smoke_evidence(evidence_dir=evidence_dir)
