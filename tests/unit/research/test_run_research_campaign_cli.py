from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research.artifact_graph import ResearchArtifactGraph
from qts.research.audit_log import ResearchAuditLog

from scripts import run_research
from tests.unit.research.engine.test_autonomous_engine_trial_generation import (
    force_clean_reproducibility,
)


def test_campaign_validate_writes_audit_and_artifact_graph(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    campaign_path = Path("configs/research/campaigns/gc_si_autonomous_v1.yaml")

    exit_code = run_research.main(
        [
            "campaign",
            "validate",
            "--campaign",
            str(campaign_path),
            "--audit-log-root",
            str(tmp_path / "audit"),
            "--artifact-graph-root",
            str(tmp_path / "graphs"),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["campaign_id"] == "gc_si_autonomous_v1"
    assert str(payload["campaign_hash"]).startswith("sha256:")
    records = ResearchAuditLog(tmp_path / "audit").list()
    assert [record.record_type for record in records] == [
        "campaign_loaded",
        "artifact_graph_written",
    ]
    graph = ResearchArtifactGraph.from_payload(
        json.loads((tmp_path / "graphs" / "campaign-gc_si_autonomous_v1.json").read_text())
    )
    graph.validate()
    assert {node.node_type for node in graph.nodes} == {"campaign"}


def test_campaign_validate_rejects_invalid_campaign(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("campaign_id: bad\nuniverse: [GC]\n", encoding="utf-8")

    exit_code = run_research.main(["campaign", "validate", "--campaign", str(invalid)])

    assert exit_code == 2
    assert "universe must be a mapping" in capsys.readouterr().err


def test_campaign_run_and_status_honestly_reject_toy_fixture(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # WIRING + HONESTY: the campaign CLI runs the pipeline end-to-end on a toy
    # fixture, produces the full honest artifact set (validation summary, fitness
    # landscape, rejected candidates with reasons, verifiable audit chain), and
    # honestly rejects because no candidate clears the OOS / multiplicity bar.
    # Promotion is NOT faked; rejection is the correct outcome to assert.
    force_clean_reproducibility(monkeypatch)
    output_root = tmp_path / "campaign"
    data_paths = _write_data_paths(tmp_path)

    exit_code = run_research.main(
        [
            "campaign",
            "run",
            "--campaign",
            "configs/research/campaigns/gc_si_autonomous_v1.yaml",
            "--output-root",
            str(output_root),
            "--data-path",
            f"GC={data_paths['GC']}",
            "--data-path",
            f"SI={data_paths['SI']}",
        ]
    )

    # Honest rejection is reported with a non-zero exit and an honest status.
    assert exit_code == 1
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["accepted"] is False
    assert run_payload["status"] == "rejected"

    # WIRING: every honest artifact the pipeline must emit exists.
    for relative_path in (
        "validation_summary.json",
        "fitness_landscape.jsonl",
        "rejected_candidates.jsonl",
        "selected_candidates.jsonl",
        "audit/audit_log.jsonl",
        "artifact_graph/artifact_graph.json",
        "report.md",
    ):
        assert (output_root / relative_path).exists(), relative_path

    # HONESTY: no candidate promoted; every rejection carries a recorded reason.
    selected_rows = _jsonl(output_root / "selected_candidates.jsonl")
    rejected_rows = _jsonl(output_root / "rejected_candidates.jsonl")
    landscape_rows = _jsonl(output_root / "fitness_landscape.jsonl")
    assert selected_rows == []
    assert rejected_rows
    assert all(row["reasons"] for row in rejected_rows)
    assert len(landscape_rows) == len(selected_rows) + len(rejected_rows)

    validation_summary = json.loads((output_root / "validation_summary.json").read_text())
    assert validation_summary["status"] == "rejected"
    assert validation_summary["promotion_packet_count"] == 0
    assert validation_summary["rejected_candidate_count"] == len(rejected_rows)

    # WIRING: the audit chain is intact and the artifact graph is structurally
    # valid (a rejected campaign has no promotion sub-chain, so the basic graph
    # contract is asserted rather than the release full-chain).
    assert ResearchAuditLog(output_root / "audit" / "audit_log.jsonl").verify_hash_chain() == ()
    graph = ResearchArtifactGraph.from_payload(
        json.loads((output_root / "artifact_graph" / "artifact_graph.json").read_text())
    )
    graph.validate()

    # WIRING: the status command reflects the same honest rejected verdict.
    status_exit = run_research.main(["campaign", "status", "--output-root", str(output_root)])
    assert status_exit == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload["status"] == "rejected"
    assert status_payload["promotion_packet_count"] == 0
    assert status_payload["rejected_candidate_count"] == len(rejected_rows)


def test_campaign_resume_requires_approved_generation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_root = tmp_path / "campaign"
    output_root.mkdir()
    (output_root / "campaign_state.json").write_text(
        json.dumps({"status": "pending_human_approval"}),
        encoding="utf-8",
    )

    exit_code = run_research.main(["campaign", "resume", "--output-root", str(output_root)])

    assert exit_code == 2
    assert "campaign resume requires an approved next-generation state" in capsys.readouterr().err


def test_campaign_approval_rejects_changed_proposal_hash(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    proposal = tmp_path / "proposal.json"
    proposal.write_text(
        json.dumps({"proposal_hash": "sha256:actual", "proposal_id": "proposal-1"}),
        encoding="utf-8",
    )

    exit_code = run_research.main(
        [
            "campaign",
            "approve-next-generation",
            "--proposal",
            str(proposal),
            "--expected-proposal-hash",
            "sha256:expected",
            "--decision",
            "approved",
            "--reviewer",
            "research-lead",
            "--reason",
            "reviewed",
        ]
    )

    assert exit_code == 2
    assert "proposal hash mismatch" in capsys.readouterr().err


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_data_paths(tmp_path: Path) -> dict[str, Path]:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return {
        "GC": _write_bars(data_dir / "gc.csv", 100),
        "SI": _write_bars(data_dir / "si.csv", 101),
    }


def _write_bars(path: Path, base: int) -> Path:
    path.write_text(
        "\n".join(
            ["timestamp,close"]
            + [
                f"2026-01-02T00:{minute:02d}:00+00:00,{price:.1f}"
                for minute, price in enumerate(_profit_factor_fixture_prices(base))
            ]
            + [""]
        ),
        encoding="utf-8",
    )
    return path


def _profit_factor_fixture_prices(base: int) -> tuple[int, ...]:
    return (
        *((base,) * 15),
        base + 1,
        base,
        base - 1,
        *((base - 1,) * 15),
        base,
        base + 3,
        base + 6,
        base + 9,
        base + 12,
        base + 8,
        base + 4,
        *((base + 4,) * 10),
    )
