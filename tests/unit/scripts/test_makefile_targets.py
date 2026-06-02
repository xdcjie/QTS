from pathlib import Path


def test_integration_target_excludes_full_data_release_tests() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert 'test-integration:\n\tuv run pytest tests/integration -m "not full_data"' in makefile


def test_final_readiness_runs_full_data_release_tests() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "test-full-data:" in makefile
    assert "uv run pytest tests/integration -m full_data" in makefile
    assert "final-product-guardrails:" in makefile
    assert "scripts/verify_final_readiness.py" in makefile
    assert "final-readiness: final-product-guardrails readiness-check test-full-data" in makefile


def test_full_data_pytest_marker_is_registered() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert '"full_data: release-grade tests that use full historical datasets",' in pyproject


def test_guardrails_target_sets_backend_pythonpath() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    expected = "guardrails:\n\tPYTHONPATH=backend/src uv run python scripts/verify_guardrails.py"

    assert expected in makefile


def test_external_readiness_target_validates_evidence_directory() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "QTS_EXTERNAL_EVIDENCE_DIR ?= evidence/ibkr" in makefile
    assert "scripts/generate_external_readiness_smoke_evidence.py" in makefile
    assert "--evidence-dir $(QTS_EXTERNAL_EVIDENCE_DIR)" in makefile
