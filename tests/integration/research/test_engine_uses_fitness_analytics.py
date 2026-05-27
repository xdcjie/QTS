from __future__ import annotations

import json
from pathlib import Path

from tests.integration.research._autonomous_engine_plan_helpers import run_engine


def test_engine_uses_fitness_analytics_from_landscape(tmp_path: Path) -> None:
    _, result = run_engine(
        tmp_path,
        families=("momentum", "breakout"),
        max_trials_per_generation=4,
        max_total_trials=4,
    )

    payload = json.loads(result.fitness_analytics_path.read_text(encoding="utf-8"))
    assert payload["analytics_hash"].startswith("sha256:")
    assert payload["best_family"]
    assert payload["parameter_regions"]
    assert payload["regime_summaries"]
    assert "rejection_clusters" in payload
