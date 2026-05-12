from pathlib import Path


def test_guardrails_target_sets_backend_pythonpath() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")
    expected = "guardrails:\n\tPYTHONPATH=backend/src uv run python scripts/verify_guardrails.py"

    assert expected in makefile
