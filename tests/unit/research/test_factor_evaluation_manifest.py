from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from qts.research import ExperimentManifestConfig, ExperimentManifestWriter
from qts.research.factor_evaluation import (
    FactorEvaluationArtifactWriter,
    FactorEvaluationMetrics,
    FactorEvaluationResult,
)


def test_factor_evaluation_artifact_is_hashed_by_experiment_manifest(
    tmp_path: Path,
) -> None:
    artifact_writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluation")
    artifact_path = artifact_writer.write(
        FactorEvaluationResult(
            as_of=date(2026, 1, 2),
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal("1"),
                long_short_spread=Decimal("0.05"),
                coverage=Decimal("1"),
                turnover=None,
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )
    expected_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"

    result = ExperimentManifestWriter(tmp_path / "artifacts" / "research").write_manifest(
        ExperimentManifestConfig(
            experiment_id="exp-factor-evaluation",
            strategy_name="research-screen",
            strategy_version="1",
            factor_versions={"momentum": "1"},
            dataset_ids=["daily-bars-v1"],
            config={"forward_return_horizon": "1d"},
            artifact_paths=[artifact_path],
            metrics={"rank_ic": "1"},
        )
    )

    payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert payload["artifact_hashes"] == {artifact_path.name: expected_hash}
    assert payload["artifact_paths_by_hash"] == {expected_hash: str(artifact_path)}
