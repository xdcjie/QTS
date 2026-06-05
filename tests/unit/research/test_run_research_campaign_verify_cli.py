from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from scripts import run_research


def test_campaign_verify_rejects_missing_release_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_root = tmp_path / "missing-campaign"

    exit_code = run_research.main(["campaign", "verify", "--output-root", str(output_root)])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert payload["criteria"]["validation_summary"]["accepted"] is False
    assert payload["criteria"]["artifact_graph"]["accepted"] is False
    assert (output_root / "release_verification.json").exists()


def test_campaign_verify_rejects_pending_human_approval_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_root = tmp_path / "pending-campaign"
    output_root.mkdir()
    (output_root / "campaign_state.json").write_text(
        json.dumps({"status": "pending_human_approval"}, sort_keys=True),
        encoding="utf-8",
    )

    exit_code = run_research.main(["campaign", "verify", "--output-root", str(output_root)])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert payload["criteria"]["campaign_state"]["accepted"] is False
    assert payload["criteria"]["campaign_state"]["status"] == "pending_human_approval"


def test_campaign_verify_records_clean_engine_parity_evidence(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "campaign"
    evidence_path = _write_engine_parity_evidence(tmp_path, status="ok")

    payload = run_research._verify_campaign_release_bundle(
        output_root,
        engine_parity_evidence=evidence_path,
    )

    criterion = payload["criteria"]["engine_parity_evidence"]
    assert criterion["accepted"] is True
    assert criterion["path"] == str(evidence_path)
    assert criterion["candidate_replaces_reference"] is False


def test_campaign_verify_rejects_unclean_engine_parity_evidence(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "campaign"
    evidence_path = _write_engine_parity_evidence(tmp_path, status="failed")

    payload = run_research._verify_campaign_release_bundle(
        output_root,
        engine_parity_evidence=evidence_path,
    )

    criterion = payload["criteria"]["engine_parity_evidence"]
    assert payload["accepted"] is False
    assert criterion["accepted"] is False
    assert "engine parity status is not ok: failed" in criterion["reasons"]


def test_campaign_verify_rejects_replacement_engine_parity_evidence(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "campaign"
    evidence_path = _write_engine_parity_evidence(
        tmp_path,
        status="ok",
        candidate_replaces_reference=True,
    )

    payload = run_research._verify_campaign_release_bundle(
        output_root,
        engine_parity_evidence=evidence_path,
    )

    criterion = payload["criteria"]["engine_parity_evidence"]
    assert payload["accepted"] is False
    assert criterion["accepted"] is False
    assert (
        "engine parity evidence must declare candidate_replaces_reference=false"
        in criterion["reasons"]
    )


def test_campaign_verify_rejects_non_shadow_engine_parity_evidence(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "campaign"
    evidence_path = _write_engine_parity_evidence(
        tmp_path,
        status="ok",
        engine_mode="replacement",
    )

    payload = run_research._verify_campaign_release_bundle(
        output_root,
        engine_parity_evidence=evidence_path,
    )

    criterion = payload["criteria"]["engine_parity_evidence"]
    assert payload["accepted"] is False
    assert criterion["accepted"] is False
    assert "engine parity evidence must declare engine_mode=shadow" in criterion["reasons"]


def test_campaign_verify_rejects_wrong_engine_identity(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "campaign"
    evidence_path = _write_engine_parity_evidence(
        tmp_path,
        status="ok",
        engine_id="python",
        reference_engine="rust",
    )

    payload = run_research._verify_campaign_release_bundle(
        output_root,
        engine_parity_evidence=evidence_path,
    )

    criterion = payload["criteria"]["engine_parity_evidence"]
    assert payload["accepted"] is False
    assert criterion["accepted"] is False
    assert "engine parity evidence must declare engine_id=rust" in criterion["reasons"]
    assert "engine parity evidence must declare reference_engine=python" in criterion["reasons"]


def test_campaign_verify_rejects_engine_parity_evidence_missing_roll_diff(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "campaign"
    evidence_path = _write_engine_parity_evidence(
        tmp_path,
        status="ok",
        phases=("phase2_replay_sequence_diff", "phase3_engine_backtest_diff"),
    )

    payload = run_research._verify_campaign_release_bundle(
        output_root,
        engine_parity_evidence=evidence_path,
    )

    criterion = payload["criteria"]["engine_parity_evidence"]
    assert payload["accepted"] is False
    assert criterion["accepted"] is False
    assert any("phase3_continuous_future_roll_diff" in reason for reason in criterion["reasons"])


def _write_engine_parity_evidence(
    tmp_path: Path,
    *,
    status: str,
    candidate_replaces_reference: bool = False,
    engine_id: str = "rust",
    engine_mode: str = "shadow",
    reference_engine: str = "python",
    phases: tuple[str, ...] = (
        "phase2_replay_sequence_diff",
        "phase3_engine_backtest_diff",
        "phase3_continuous_future_roll_diff",
    ),
) -> Path:
    path = tmp_path / f"engine-parity-{status}.json"
    diff_artifacts = _write_engine_parity_diff_artifacts(tmp_path, phases=phases)
    path.write_text(
        json.dumps(
            {
                "checked": ["phase1", "phase2", "phase3", "phase4"],
                "candidate_replaces_reference": candidate_replaces_reference,
                "diff_artifacts": diff_artifacts,
                "engine_id": engine_id,
                "engine_mode": engine_mode,
                "reference_engine": reference_engine,
                "status": status,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_engine_parity_diff_artifacts(
    tmp_path: Path,
    *,
    phases: tuple[str, ...],
) -> list[dict[str, object]]:
    artifacts: list[dict[str, object]] = []
    for phase in phases:
        path = tmp_path / f"{phase}.json"
        path.write_text(
            json.dumps(
                {
                    "artifact_type": "python_rust_parity_diff",
                    "candidate_engine": "rust",
                    "differences": [],
                    "phase": phase,
                    "reference_engine": "python",
                    "status": "clean",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        artifacts.append(
            {
                "phase": phase,
                "path": str(path),
                "sha256": f"sha256:{sha256(path.read_bytes()).hexdigest()}",
                "status": "clean",
            }
        )
    return artifacts
