from __future__ import annotations

from pathlib import Path

from qts.quality.rules.research import TradeDiagnosticsRequiredForPaperRule


def _write_candidate(repo_root: Path, body: str) -> Path:
    candidate_dir = repo_root / "configs" / "research" / "promotion"
    candidate_dir.mkdir(parents=True)
    path = candidate_dir / "candidate.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_paper_readiness_guardrail_requires_verified_evidence_bundle(tmp_path: Path) -> None:
    _write_candidate(
        tmp_path,
        """
promotion_candidate_id: pc-vwap
status: paper_candidate
evidence_bundle_id: evb_001
idea_id: idea-vwap
paper_readiness:
  evidence_bundle_verified: false
  trade_diagnostics_available: true
  validation_scorecard_available: true
  cost_stress_available: true
  no_research_import_in_production: true
  no_examples_direct_promotion: true
""",
    )

    violations = TradeDiagnosticsRequiredForPaperRule().check_repository(tmp_path)

    assert [violation.code for violation in violations] == [
        "TRADE_DIAGNOSTICS_REQUIRED_FOR_PAPER"
    ]
    assert "evidence_bundle_verified" in violations[0].message


def test_paper_readiness_guardrail_requires_import_boundary_checks(tmp_path: Path) -> None:
    _write_candidate(
        tmp_path,
        """
promotion_candidate_id: pc-vwap
status: small_live_candidate
evidence_bundle_id: evb_001
idea_id: idea-vwap
paper_readiness:
  evidence_bundle_verified: true
  trade_diagnostics_available: true
  validation_scorecard_available: true
  cost_stress_available: true
  no_research_import_in_production: false
  no_examples_direct_promotion: true
""",
    )

    violations = TradeDiagnosticsRequiredForPaperRule().check_repository(tmp_path)

    assert len(violations) == 1
    assert "no_research_import_in_production" in violations[0].message


def test_paper_readiness_guardrail_accepts_full_readiness(tmp_path: Path) -> None:
    _write_candidate(
        tmp_path,
        """
promotion_candidate_id: pc-vwap
status: paper_candidate
evidence_bundle_id: evb_001
idea_id: idea-vwap
paper_readiness:
  evidence_bundle_verified: true
  trade_diagnostics_available: true
  validation_scorecard_available: true
  cost_stress_available: true
  no_research_import_in_production: true
  no_examples_direct_promotion: true
""",
    )

    assert TradeDiagnosticsRequiredForPaperRule().check_repository(tmp_path) == []
