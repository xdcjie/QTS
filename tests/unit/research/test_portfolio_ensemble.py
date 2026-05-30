from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


def _evaluate_portfolio_ensemble() -> Any:
    from qts.research.portfolio_ensemble import evaluate_portfolio_ensemble

    return evaluate_portfolio_ensemble


def _scan_portfolio_ensemble_allocations() -> Any:
    from qts.research.portfolio_ensemble import (
        scan_portfolio_ensemble_allocations,
    )

    return scan_portfolio_ensemble_allocations


def _scan_volatility_managed_allocations() -> Any:
    from qts.research.portfolio_ensemble import (
        scan_volatility_managed_allocations,
    )

    return scan_volatility_managed_allocations


def _leg(name: str, manifest_path: Path, weight: str = "1") -> dict[str, str]:
    return {"manifest_path": str(manifest_path), "name": name, "weight": weight}


def _write_manifest(
    tmp_path: Path,
    name: str,
    rows: tuple[tuple[datetime, Decimal], ...],
    *,
    artifact_name: str | None = None,
) -> Path:
    artifact_path = tmp_path / (artifact_name or f"{name}.equity_curve.ndjson")
    artifact_path.write_text(
        "".join(
            json.dumps(
                {"time": timestamp.isoformat(), "equity": str(equity)},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
            for timestamp, equity in rows
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / f"{name}.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifacts": {
                    "equity_curve": {
                        "path": artifact_path.name,
                        "rows": len(rows),
                        "sha256": f"sha256:{name}",
                    }
                },
                "runtime_mode": "backtest",
                "run_id": name,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path


def test_portfolio_ensemble_aligns_manifest_equity_curves_without_lookahead(
    tmp_path: Path,
) -> None:
    evaluate_portfolio_ensemble = _evaluate_portfolio_ensemble()
    manifest_a = _write_manifest(
        tmp_path,
        "a",
        (
            (datetime(2020, 1, 2, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 3, tzinfo=UTC), Decimal("110")),
            (datetime(2020, 1, 4, tzinfo=UTC), Decimal("121")),
        ),
    )
    manifest_b = _write_manifest(
        tmp_path,
        "b",
        (
            (datetime(2020, 1, 1, tzinfo=UTC), Decimal("200")),
            (datetime(2020, 1, 3, tzinfo=UTC), Decimal("180")),
            (datetime(2020, 1, 4, tzinfo=UTC), Decimal("220")),
        ),
    )

    result = evaluate_portfolio_ensemble(
        {
            "allocation_name": "equal",
            "legs": (_leg("a", manifest_a), _leg("b", manifest_b)),
        }
    )

    assert [(point["time"], Decimal(point["equity"])) for point in result["equity_curve"]] == [
        ("2020-01-02T00:00:00+00:00", Decimal("1.0")),
        ("2020-01-03T00:00:00+00:00", Decimal("1.00")),
        ("2020-01-04T00:00:00+00:00", Decimal("1.155")),
    ]
    assert Decimal(result["metrics"]["total_return"]) == Decimal("0.155")
    assert Decimal(result["metrics"]["max_drawdown"]) == Decimal("0")
    assert result["not_tradable_config"] is True
    assert result["research_only"] is True
    assert result["source_manifest_paths"] == [str(manifest_a), str(manifest_b)]


def test_portfolio_ensemble_normalizes_positive_weights_and_reports_drawdown(
    tmp_path: Path,
) -> None:
    evaluate_portfolio_ensemble = _evaluate_portfolio_ensemble()
    manifest_a = _write_manifest(
        tmp_path,
        "a",
        (
            (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 2, tzinfo=UTC), Decimal("80")),
            (datetime(2020, 1, 3, tzinfo=UTC), Decimal("100")),
        ),
    )
    manifest_b = _write_manifest(
        tmp_path,
        "b",
        (
            (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 2, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 3, tzinfo=UTC), Decimal("100")),
        ),
    )

    result = evaluate_portfolio_ensemble(
        {
            "allocation_name": "weighted",
            "legs": (_leg("a", manifest_a, "2"), _leg("b", manifest_b)),
        }
    )

    assert Decimal(result["equity_curve"][1]["equity"]).quantize(Decimal("0.000001")) == Decimal(
        "0.866667"
    )
    assert Decimal(result["metrics"]["max_drawdown"]).quantize(Decimal("0.000001")) == Decimal(
        "0.133333"
    )


def test_portfolio_ensemble_collapses_duplicate_timestamps_to_latest_equity(
    tmp_path: Path,
) -> None:
    evaluate_portfolio_ensemble = _evaluate_portfolio_ensemble()
    manifest_a = _write_manifest(
        tmp_path,
        "a",
        (
            (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 2, tzinfo=UTC), Decimal("105")),
            (datetime(2020, 1, 2, tzinfo=UTC), Decimal("110")),
            (datetime(2020, 1, 3, tzinfo=UTC), Decimal("121")),
        ),
    )
    manifest_b = _write_manifest(
        tmp_path,
        "b",
        (
            (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 2, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 3, tzinfo=UTC), Decimal("100")),
        ),
    )

    result = evaluate_portfolio_ensemble(
        {
            "allocation_name": "duplicates",
            "legs": (_leg("a", manifest_a), _leg("b", manifest_b)),
        }
    )

    assert [(point["time"], Decimal(point["equity"])) for point in result["equity_curve"]] == [
        ("2020-01-01T00:00:00+00:00", Decimal("1.0")),
        ("2020-01-02T00:00:00+00:00", Decimal("1.05")),
        ("2020-01-03T00:00:00+00:00", Decimal("1.105")),
    ]


def test_portfolio_ensemble_can_report_metrics_on_daily_utc_grid(tmp_path: Path) -> None:
    evaluate_portfolio_ensemble = _evaluate_portfolio_ensemble()
    manifest_a = _write_manifest(
        tmp_path,
        "a",
        (
            (datetime(2020, 1, 1, 10, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 1, 11, tzinfo=UTC), Decimal("80")),
            (datetime(2020, 1, 2, 10, tzinfo=UTC), Decimal("120")),
            (datetime(2020, 1, 2, 11, tzinfo=UTC), Decimal("110")),
            (datetime(2020, 1, 3, 10, tzinfo=UTC), Decimal("121")),
        ),
    )
    manifest_b = _write_manifest(
        tmp_path,
        "b",
        (
            (datetime(2020, 1, 1, 10, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 2, 10, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 3, 10, tzinfo=UTC), Decimal("100")),
        ),
    )

    result = evaluate_portfolio_ensemble(
        {
            "allocation_name": "daily",
            "legs": (_leg("a", manifest_a), _leg("b", manifest_b)),
            "reporting_grid": "daily_utc",
        }
    )

    assert result["reporting_grid"] == "daily_utc"
    assert result["metric_point_count"] == 3
    assert result["point_count"] == 5
    assert Decimal(result["metrics"]["total_return"]) == Decimal("0.105")
    assert Decimal(result["metrics"]["max_drawdown"]) == Decimal("0")
    assert Decimal(result["full_curve_metrics"]["max_drawdown"]) == Decimal("0.1")


def test_portfolio_ensemble_rejects_missing_equity_curve_artifact(tmp_path: Path) -> None:
    evaluate_portfolio_ensemble = _evaluate_portfolio_ensemble()
    manifest_path = tmp_path / "missing.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifacts": {
                    "equity_curve": {
                        "path": "missing.equity_curve.ndjson",
                        "rows": 2,
                        "sha256": "sha256:missing",
                    }
                },
                "runtime_mode": "backtest",
                "run_id": "missing",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="equity curve artifact not found"):
        evaluate_portfolio_ensemble(
            {"allocation_name": "missing", "legs": (_leg("missing", manifest_path),)}
        )


def test_portfolio_ensemble_rejects_partial_equity_curve_artifact(tmp_path: Path) -> None:
    evaluate_portfolio_ensemble = _evaluate_portfolio_ensemble()
    manifest_path = _write_manifest(
        tmp_path,
        "partial",
        (
            (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
            (datetime(2020, 1, 2, tzinfo=UTC), Decimal("101")),
        ),
        artifact_name=".equity_curve.partial.ndjson",
    )

    with pytest.raises(ValueError, match="partial equity curve artifact"):
        evaluate_portfolio_ensemble(
            {"allocation_name": "partial", "legs": (_leg("partial", manifest_path),)}
        )


def test_portfolio_ensemble_scan_ranks_weight_grid_and_marks_constraints(
    tmp_path: Path,
) -> None:
    scan_portfolio_ensemble_allocations = _scan_portfolio_ensemble_allocations()
    period_manifests = {
        "anchor": {
            "steady": _write_manifest(
                tmp_path,
                "steady-anchor",
                (
                    (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
                    (datetime(2021, 1, 1, tzinfo=UTC), Decimal("110")),
                ),
            ),
            "burst": _write_manifest(
                tmp_path,
                "burst-anchor",
                (
                    (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
                    (datetime(2021, 1, 1, tzinfo=UTC), Decimal("90")),
                ),
            ),
        },
        "validation": {
            "steady": _write_manifest(
                tmp_path,
                "steady-validation",
                (
                    (datetime(2021, 1, 1, tzinfo=UTC), Decimal("100")),
                    (datetime(2022, 1, 1, tzinfo=UTC), Decimal("105")),
                ),
            ),
            "burst": _write_manifest(
                tmp_path,
                "burst-validation",
                (
                    (datetime(2021, 1, 1, tzinfo=UTC), Decimal("100")),
                    (datetime(2022, 1, 1, tzinfo=UTC), Decimal("130")),
                ),
            ),
        },
    }

    result = scan_portfolio_ensemble_allocations(
        {
            "scan_name": "unit",
            "reporting_grid": "daily_utc",
            "weight_step": "0.5",
            "top_n": 3,
            "periods": ["anchor", "validation"],
            "baseline_period": "anchor",
            "post_periods": ["validation"],
            "constraints": {
                "min_baseline_annual_return": "0",
                "min_post_annual_return": "0.10",
                "max_full_drawdown": "0.20",
            },
            "candidates": [
                {
                    "name": "steady",
                    "period_manifests": {
                        period: str(paths["steady"]) for period, paths in period_manifests.items()
                    },
                },
                {
                    "name": "burst",
                    "period_manifests": {
                        period: str(paths["burst"]) for period, paths in period_manifests.items()
                    },
                },
            ],
        }
    )

    assert result["scan_name"] == "unit"
    assert result["candidate_count"] == 2
    assert result["evaluated_allocation_count"] == 3
    assert result["allocation_overfit_warning"] == (
        "Allocation scan is research-only evidence and is not a tradable runtime config."
    )
    assert result["not_tradable_config"] is True
    assert result["report_only_periods"] == []
    assert result["research_only"] is True
    assert result["score_periods"] == ["anchor", "validation"]
    assert result["satisfying_allocation_count"] == 1
    assert result["top_allocations"][0]["weights"] == {"burst": "0.5", "steady": "0.5"}
    assert result["top_allocations"][0]["meets_constraints"] is True
    assert result["top_allocations"][0]["metrics"]["validation"]["annual_return"] > "0.10"


@pytest.mark.parametrize("score_field", ("baseline_period", "post_periods", "score_periods"))
def test_portfolio_scan_rejects_holdout_in_all_score_fields(
    tmp_path: Path,
    score_field: str,
) -> None:
    scan_portfolio_ensemble_allocations = _scan_portfolio_ensemble_allocations()
    manifests = {
        period: _write_manifest(
            tmp_path,
            f"steady-{period}",
            (
                (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
                (datetime(2021, 1, 1, tzinfo=UTC), Decimal("110")),
            ),
        )
        for period in ("anchor", "holdout")
    }
    payload: dict[str, Any] = {
        "scan_name": "unsafe",
        "periods": ["anchor", "holdout"],
        "period_roles": {
            "anchor": "anchor",
            "holdout": "holdout_report_only",
        },
        "baseline_period": "anchor",
        "post_periods": ["anchor"],
        "score_periods": ["anchor"],
        "candidates": [
            {
                "name": "steady",
                "period_manifests": {period: str(path) for period, path in manifests.items()},
            },
        ],
    }
    if score_field == "baseline_period":
        payload["baseline_period"] = "holdout"
    else:
        payload[score_field] = ["holdout"]

    with pytest.raises(ValueError, match=rf"report-only period.*{score_field}"):
        scan_portfolio_ensemble_allocations(payload)


def test_portfolio_scan_artifact_records_score_and_report_only_periods(tmp_path: Path) -> None:
    scan_portfolio_ensemble_allocations = _scan_portfolio_ensemble_allocations()
    manifests = {
        period: _write_manifest(
            tmp_path,
            f"steady-{period}",
            (
                (datetime(2020, 1, 1, tzinfo=UTC), Decimal("100")),
                (datetime(2021, 1, 1, tzinfo=UTC), Decimal("110")),
            ),
        )
        for period in ("anchor", "validation", "holdout")
    }

    result = scan_portfolio_ensemble_allocations(
        {
            "scan_name": "period-roles",
            "periods": ["anchor", "validation", "holdout"],
            "period_roles": {
                "anchor": "anchor",
                "validation": "validation",
                "holdout": "holdout_report_only",
            },
            "baseline_period": "anchor",
            "post_periods": ["validation"],
            "score_periods": ["anchor", "validation"],
            "candidates": [
                {
                    "name": "steady",
                    "period_manifests": {period: str(path) for period, path in manifests.items()},
                },
            ],
        }
    )

    assert result["score_periods"] == ["anchor", "validation"]
    assert result["report_only_periods"] == ["holdout"]


def test_volatility_managed_scan_uses_only_prior_returns_for_weights(
    tmp_path: Path,
) -> None:
    scan_volatility_managed_allocations = _scan_volatility_managed_allocations()
    manifests = {
        "steady": _write_manifest(
            tmp_path,
            "steady",
            (
                (datetime(2021, 1, 1, tzinfo=UTC), Decimal("100")),
                (datetime(2021, 1, 2, tzinfo=UTC), Decimal("101")),
                (datetime(2021, 1, 3, tzinfo=UTC), Decimal("102")),
                (datetime(2021, 1, 4, tzinfo=UTC), Decimal("103")),
            ),
        ),
        "burst": _write_manifest(
            tmp_path,
            "burst",
            (
                (datetime(2021, 1, 1, tzinfo=UTC), Decimal("100")),
                (datetime(2021, 1, 2, tzinfo=UTC), Decimal("90")),
                (datetime(2021, 1, 3, tzinfo=UTC), Decimal("130")),
                (datetime(2021, 1, 4, tzinfo=UTC), Decimal("140")),
            ),
        ),
    }

    result = scan_volatility_managed_allocations(
        {
            "scan_name": "unit-dynamic",
            "reporting_grid": "daily_utc",
            "periods": ["validation"],
            "selection_periods": ["validation"],
            "post_selection_periods": ["validation"],
            "constraints": {
                "min_selection_post_annual_return": "-1",
                "max_selection_drawdown": "1",
            },
            "parameter_grid": {
                "lookback_days": [1],
                "min_history_days": [1],
                "min_trailing_return": ["-1"],
                "top_n_legs": [1],
                "target_annual_vol": ["10"],
                "max_gross_exposure": ["1"],
                "max_leg_weight": ["1"],
            },
            "candidates": [
                {"name": name, "period_manifests": {"validation": str(path)}}
                for name, path in manifests.items()
            ],
        }
    )

    top = result["top_allocations"][0]
    validation = top["metrics"]["validation"]
    assert result["evaluated_parameter_count"] == 1
    assert result["allocation_overfit_warning"] == (
        "Allocation scan is research-only evidence and is not a tradable runtime config."
    )
    assert result["not_tradable_config"] is True
    assert result["post_selection_periods"] == ["validation"]
    assert result["report_only_periods"] == []
    assert result["research_only"] is True
    assert result["selection_periods"] == ["validation"]
    assert result["uses_prior_returns_only"] is True
    assert top["parameters"]["lookback_days"] == 1
    assert Decimal(validation["total_return"]).quantize(Decimal("0.0001")) == Decimal("0.0876")
    assert Decimal(validation["total_return"]) < Decimal("0.20")
