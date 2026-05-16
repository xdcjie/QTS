from pathlib import Path


def test_guardrails_target_sets_backend_pythonpath() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    expected = "guardrails:\n\tPYTHONPATH=backend/src uv run python scripts/verify_guardrails.py"

    assert expected in makefile


def test_external_readiness_target_validates_evidence_directory() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "QTS_EXTERNAL_EVIDENCE_DIR ?= evidence/ibkr" in makefile
    assert "scripts/generate_external_readiness_smoke_evidence.py" in makefile
    assert "--evidence-dir $(QTS_EXTERNAL_EVIDENCE_DIR)" in makefile
