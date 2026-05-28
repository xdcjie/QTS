from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.integration.research.test_gc_si_autonomous_real_pipeline_acceptance import (
    test_gc_si_autonomous_real_pipeline_acceptance_cli as _run_gc_si_acceptance,
)


def test_gc_si_real_strategy_research_acceptance(tmp_path: Path, capsys: Any) -> None:
    _run_gc_si_acceptance(tmp_path, capsys)
