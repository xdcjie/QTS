from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research.artifact_graph import ResearchArtifactGraph
from qts.research.audit_log import ResearchAuditLog

from scripts import run_research


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


def test_campaign_run_status_stop_resume_and_approval(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
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

    assert exit_code == 0
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["status"] == "accepted"

    status_exit = run_research.main(["campaign", "status", "--output-root", str(output_root)])
    assert status_exit == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload["status"] == "accepted"

    proposal = json.loads((output_root / "next_generation_proposal.json").read_text())
    approval_exit = run_research.main(
        [
            "campaign",
            "approve-next-generation",
            "--proposal",
            str(output_root / "next_generation_proposal.json"),
            "--expected-proposal-hash",
            proposal["proposal_hash"],
            "--decision",
            "approved",
            "--reviewer",
            "research-lead",
            "--reason",
            "bounded evidence supports the next generation",
            "--audit-log-root",
            str(tmp_path / "approval-audit"),
        ]
    )
    assert approval_exit == 0
    approval_payload = json.loads(capsys.readouterr().out)
    assert approval_payload["accepted"] is True

    assert (
        run_research.main(
            [
                "campaign",
                "stop",
                "--output-root",
                str(output_root),
                "--audit-log-root",
                str(tmp_path / "state-audit"),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "stopped"
    assert (
        run_research.main(
            [
                "campaign",
                "resume",
                "--output-root",
                str(output_root),
                "--audit-log-root",
                str(tmp_path / "state-audit"),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "running"


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
            [
                "timestamp,close",
                f"2026-01-02T00:00:00+00:00,{base}.0",
                f"2026-01-02T00:01:00+00:00,{base}.5",
                f"2026-01-02T00:02:00+00:00,{base + 1}.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path
