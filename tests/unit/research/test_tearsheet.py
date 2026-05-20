from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from qts.research.factor_evaluation import (
    FactorEvaluationArtifactWriter,
    FactorEvaluationMetrics,
    FactorEvaluationResult,
)
from qts.research.tearsheet import (
    FactorEvaluationTearsheet,
    FactorEvaluationTearsheetArtifactWriter,
    FactorEvaluationTearsheetMetrics,
)


def _evaluation(
    as_of: date,
    *,
    rank_ic: str,
    spread: str,
    coverage: str,
    turnover: str | None = None,
    factor_name: str = "momentum",
    factor_version: str = "1",
    missing_symbols: tuple[str, ...] = (),
) -> FactorEvaluationResult:
    return FactorEvaluationResult(
        as_of=as_of,
        factor_name=factor_name,
        factor_version=factor_version,
        metrics=FactorEvaluationMetrics(
            rank_ic=Decimal(rank_ic),
            long_short_spread=Decimal(spread),
            coverage=Decimal(coverage),
            turnover=None if turnover is None else Decimal(turnover),
            scored_count=3,
            return_count=3 - len(missing_symbols),
            missing_symbols=missing_symbols,
        ),
    )


def test_factor_tearsheet_aggregates_snapshot_metrics() -> None:
    tearsheet = FactorEvaluationTearsheet.from_evaluations(
        (
            _evaluation(
                date(2026, 1, 3),
                rank_ic="-0.2",
                spread="0.03",
                coverage="0.9",
                turnover="0.25",
            ),
            _evaluation(
                date(2026, 1, 2),
                rank_ic="0.1",
                spread="0.01",
                coverage="0.8",
                missing_symbols=("BBB",),
            ),
            _evaluation(
                date(2026, 1, 4),
                rank_ic="0.3",
                spread="-0.01",
                coverage="0.7",
                turnover="0.75",
                missing_symbols=("AAA", "BBB"),
            ),
        )
    )

    assert tearsheet.factor_name == "momentum"
    assert tearsheet.factor_version == "1"
    assert tearsheet.metrics == FactorEvaluationTearsheetMetrics(
        snapshot_count=3,
        first_as_of=date(2026, 1, 2),
        last_as_of=date(2026, 1, 4),
        mean_rank_ic=Decimal("0.0666666667"),
        positive_rank_ic_rate=Decimal("0.6666666667"),
        mean_long_short_spread=Decimal("0.01"),
        mean_coverage=Decimal("0.8"),
        min_coverage=Decimal("0.7"),
        mean_turnover=Decimal("0.5"),
        turnover_count=2,
        missing_symbols=("AAA", "BBB"),
    )
    assert [row["as_of"] for row in tearsheet.rows()] == [
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
    ]
    assert tearsheet.manifest_metrics() == {
        "mean_coverage": "0.8",
        "mean_long_short_spread": "0.01",
        "mean_rank_ic": "0.0666666667",
        "mean_turnover": "0.5",
        "min_coverage": "0.7",
        "positive_rank_ic_rate": "0.6666666667",
        "snapshot_count": 3,
        "turnover_count": 2,
    }


def test_factor_tearsheet_writer_writes_stable_json(tmp_path: Path) -> None:
    tearsheet = FactorEvaluationTearsheet.from_evaluations(
        (
            _evaluation(date(2026, 1, 2), rank_ic="0.1", spread="0.01", coverage="0.8"),
            _evaluation(
                date(2026, 1, 3),
                rank_ic="0.3",
                spread="0.03",
                coverage="0.9",
                turnover="0.25",
            ),
        )
    )

    writer = FactorEvaluationTearsheetArtifactWriter(tmp_path)
    left_path = writer.write(tearsheet)
    right_path = writer.write(tearsheet)
    payload = json.loads(left_path.read_text(encoding="utf-8"))

    assert left_path == right_path
    assert left_path.name == "momentum-1-tearsheet.json"
    assert left_path.read_text(encoding="utf-8").endswith("\n")
    assert payload["factor_name"] == "momentum"
    assert payload["metrics"]["mean_rank_ic"] == "0.2"
    assert payload["metrics"]["mean_turnover"] == "0.25"
    assert payload["snapshots"][0]["as_of"] == "2026-01-02"


def test_factor_tearsheet_manifest_metrics_keep_missing_turnover_as_none() -> None:
    tearsheet = FactorEvaluationTearsheet.from_evaluations(
        (
            _evaluation(date(2026, 1, 2), rank_ic="0.1", spread="0.01", coverage="0.8"),
            _evaluation(date(2026, 1, 3), rank_ic="0.3", spread="0.03", coverage="0.9"),
        )
    )

    assert tearsheet.metrics.mean_turnover is None
    assert tearsheet.manifest_metrics()["mean_turnover"] is None
    assert tearsheet.manifest_metrics()["turnover_count"] == 0


def test_factor_tearsheet_loads_factor_evaluation_artifacts(tmp_path: Path) -> None:
    writer = FactorEvaluationArtifactWriter(tmp_path / "evaluations")
    first = writer.write(
        _evaluation(date(2026, 1, 2), rank_ic="0.1", spread="0.01", coverage="0.8")
    )
    second = writer.write(
        _evaluation(
            date(2026, 1, 3),
            rank_ic="0.3",
            spread="0.03",
            coverage="0.9",
            turnover="0.25",
        )
    )

    tearsheet = FactorEvaluationTearsheet.from_artifact_paths((second, first))

    assert tearsheet.metrics.snapshot_count == 2
    assert tearsheet.metrics.mean_rank_ic == Decimal("0.2")
    assert tearsheet.rows()[0]["as_of"] == "2026-01-02"


def test_factor_tearsheet_writer_rejects_path_like_identity(tmp_path: Path) -> None:
    tearsheet = FactorEvaluationTearsheet.from_evaluations(
        (
            _evaluation(
                date(2026, 1, 2),
                rank_ic="0.1",
                spread="0.01",
                coverage="0.8",
                factor_name="momentum/unsafe",
            ),
        )
    )

    with pytest.raises(ValueError, match="factor_name must be filename-safe"):
        FactorEvaluationTearsheetArtifactWriter(tmp_path).write(tearsheet)


def test_factor_tearsheet_rejects_empty_and_mixed_identity() -> None:
    with pytest.raises(ValueError, match="at least one factor evaluation is required"):
        FactorEvaluationTearsheet.from_evaluations(())

    with pytest.raises(ValueError, match="factor evaluations must share one identity"):
        FactorEvaluationTearsheet.from_evaluations(
            (
                _evaluation(date(2026, 1, 2), rank_ic="0.1", spread="0.01", coverage="0.8"),
                _evaluation(
                    date(2026, 1, 3),
                    rank_ic="0.2",
                    spread="0.02",
                    coverage="0.9",
                    factor_name="quality",
                ),
            )
        )


def test_factor_tearsheet_to_pandas_returns_rows() -> None:
    tearsheet = FactorEvaluationTearsheet.from_evaluations(
        (
            _evaluation(date(2026, 1, 2), rank_ic="0.1", spread="0.01", coverage="0.8"),
            _evaluation(date(2026, 1, 3), rank_ic="0.2", spread="0.02", coverage="0.9"),
        )
    )

    frame = tearsheet.to_pandas()

    assert list(frame["as_of"]) == ["2026-01-02", "2026-01-03"]
    assert list(frame["rank_ic"]) == [Decimal("0.1"), Decimal("0.2")]


def test_factor_tearsheet_public_exports_are_available() -> None:
    from qts.research import (
        FactorEvaluationTearsheet as ExportedFactorEvaluationTearsheet,
    )
    from qts.research import (
        FactorEvaluationTearsheetArtifactWriter as ExportedFactorEvaluationTearsheetArtifactWriter,
    )
    from qts.research import (
        FactorEvaluationTearsheetMetrics as ExportedFactorEvaluationTearsheetMetrics,
    )

    assert ExportedFactorEvaluationTearsheet is FactorEvaluationTearsheet
    assert (
        ExportedFactorEvaluationTearsheetArtifactWriter is FactorEvaluationTearsheetArtifactWriter
    )
    assert ExportedFactorEvaluationTearsheetMetrics is FactorEvaluationTearsheetMetrics
