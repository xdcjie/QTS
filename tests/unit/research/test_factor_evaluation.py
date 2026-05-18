from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

import pytest
from qts.factors import FactorResult, FactorScore
from qts.research.factor_evaluation import (
    FactorEvaluation,
    FactorEvaluationArtifactWriter,
    FactorEvaluationInput,
    FactorEvaluationMetrics,
    FactorEvaluationResult,
)


@dataclass(frozen=True, slots=True)
class Asset:
    symbol: str


def _factor_result(*scores: tuple[Asset, str]) -> FactorResult:
    return FactorResult(ranked=tuple(FactorScore(asset, Decimal(value)) for asset, value in scores))


def test_factor_evaluation_computes_rank_ic_and_bucket_spread() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")

    evaluation = FactorEvaluation.evaluate(
        FactorEvaluationInput(
            as_of=date(2026, 1, 2),
            factor_name="momentum",
            factor_version="1",
            factor_result=_factor_result((aaa, "3"), (bbb, "2"), (ccc, "1")),
            forward_returns={
                aaa.symbol: Decimal("0.03"),
                bbb.symbol: Decimal("0.01"),
                ccc.symbol: Decimal("-0.02"),
            },
            bucket_count=3,
        )
    )

    assert evaluation.metrics.rank_ic == Decimal("1")
    assert evaluation.metrics.long_short_spread == Decimal("0.05")
    assert evaluation.metrics.coverage == Decimal("1")
    assert evaluation.metrics.scored_count == 3
    assert evaluation.metrics.return_count == 3


def test_factor_evaluation_records_coverage_and_missing_forward_returns() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")
    ddd = Asset("DDD")

    evaluation = FactorEvaluation.evaluate(
        FactorEvaluationInput(
            as_of=date(2026, 1, 2),
            factor_name="quality",
            factor_version="2",
            factor_result=_factor_result((aaa, "4"), (bbb, "3"), (ccc, "2"), (ddd, "1")),
            forward_returns={
                aaa.symbol: Decimal("0.04"),
                ccc.symbol: Decimal("0.01"),
                ddd.symbol: Decimal("-0.03"),
            },
            bucket_count=4,
        )
    )

    assert evaluation.metrics.coverage == Decimal("0.75")
    assert evaluation.metrics.scored_count == 4
    assert evaluation.metrics.return_count == 3
    assert evaluation.metrics.missing_symbols == ("BBB",)
    assert evaluation.metrics.long_short_spread == Decimal("0.07")


def test_factor_evaluation_computes_top_bucket_turnover() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")
    ddd = Asset("DDD")
    previous = _factor_result((aaa, "4"), (bbb, "3"), (ccc, "2"), (ddd, "1"))
    current = _factor_result((bbb, "4"), (ccc, "3"), (aaa, "2"), (ddd, "1"))

    evaluation = FactorEvaluation.evaluate(
        FactorEvaluationInput(
            as_of=date(2026, 1, 3),
            factor_name="momentum",
            factor_version="1",
            factor_result=current,
            previous_factor_result=previous,
            forward_returns={
                aaa.symbol: Decimal("0.01"),
                bbb.symbol: Decimal("0.05"),
                ccc.symbol: Decimal("0.03"),
                ddd.symbol: Decimal("-0.02"),
            },
            bucket_count=2,
        )
    )

    assert evaluation.metrics.turnover == Decimal("0.5")


def test_factor_evaluation_canonicalizes_non_perfect_rank_ic_across_decimal_contexts(
    tmp_path: Path,
) -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")
    ddd = Asset("DDD")
    eee = Asset("EEE")

    def evaluate_and_write(precision: int) -> tuple[Decimal, str]:
        with localcontext() as context:
            context.prec = precision
            evaluation = FactorEvaluation.evaluate(
                FactorEvaluationInput(
                    as_of=date(2026, 1, 2),
                    factor_name="momentum",
                    factor_version="1",
                    factor_result=_factor_result(
                        (aaa, "5"),
                        (bbb, "4"),
                        (ccc, "3"),
                        (ddd, "2"),
                        (eee, "1"),
                    ),
                    forward_returns={
                        aaa.symbol: Decimal("0.05"),
                        bbb.symbol: Decimal("0.03"),
                        ccc.symbol: Decimal("0.02"),
                        ddd.symbol: Decimal("0.01"),
                        eee.symbol: Decimal("0.04"),
                    },
                    bucket_count=5,
                )
            )
            path = FactorEvaluationArtifactWriter(tmp_path / str(precision)).write(evaluation)
            return evaluation.metrics.rank_ic, path.read_text(encoding="utf-8")

    low_precision_ic, low_precision_artifact = evaluate_and_write(10)
    high_precision_ic, high_precision_artifact = evaluate_and_write(50)

    assert low_precision_ic == Decimal("0.4")
    assert high_precision_ic == Decimal("0.4")
    assert json.loads(low_precision_artifact)["metrics"]["rank_ic"] == "0.4"
    assert low_precision_artifact == high_precision_artifact


def test_factor_evaluation_formats_rank_ic_independent_of_decimal_context(
    tmp_path: Path,
) -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")
    ddd = Asset("DDD")
    eee = Asset("EEE")
    fff = Asset("FFF")

    def evaluate_and_write(precision: int) -> tuple[Decimal, str]:
        with localcontext() as context:
            context.prec = precision
            evaluation = FactorEvaluation.evaluate(
                FactorEvaluationInput(
                    as_of=date(2026, 1, 2),
                    factor_name="reversal",
                    factor_version="1",
                    factor_result=_factor_result(
                        (aaa, "6"),
                        (bbb, "5"),
                        (ccc, "4"),
                        (ddd, "3"),
                        (eee, "2"),
                        (fff, "1"),
                    ),
                    forward_returns={
                        aaa.symbol: Decimal("0.06"),
                        bbb.symbol: Decimal("0.01"),
                        ccc.symbol: Decimal("0.02"),
                        ddd.symbol: Decimal("0.03"),
                        eee.symbol: Decimal("0.04"),
                        fff.symbol: Decimal("0.05"),
                    },
                    bucket_count=6,
                )
            )
            path = FactorEvaluationArtifactWriter(tmp_path / f"rank-{precision}").write(evaluation)
            return evaluation.metrics.rank_ic, path.read_text(encoding="utf-8")

    low_precision_ic, low_precision_artifact = evaluate_and_write(5)
    high_precision_ic, high_precision_artifact = evaluate_and_write(50)

    assert low_precision_ic == Decimal("-0.1428571429")
    assert high_precision_ic == Decimal("-0.1428571429")
    assert json.loads(low_precision_artifact)["metrics"]["rank_ic"] == "-0.1428571429"
    assert low_precision_artifact == high_precision_artifact


def test_factor_evaluation_computes_coverage_independent_of_decimal_context(
    tmp_path: Path,
) -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")

    def evaluate_and_write(precision: int) -> tuple[Decimal, str]:
        with localcontext() as context:
            context.prec = precision
            evaluation = FactorEvaluation.evaluate(
                FactorEvaluationInput(
                    as_of=date(2026, 1, 2),
                    factor_name="momentum",
                    factor_version="1",
                    factor_result=_factor_result((aaa, "3"), (bbb, "2"), (ccc, "1")),
                    forward_returns={
                        aaa.symbol: Decimal("0.03"),
                        bbb.symbol: Decimal("0.02"),
                    },
                    bucket_count=3,
                )
            )
            path = FactorEvaluationArtifactWriter(tmp_path / f"coverage-{precision}").write(
                evaluation
            )
            return evaluation.metrics.coverage, path.read_text(encoding="utf-8")

    low_precision_coverage, low_precision_artifact = evaluate_and_write(5)
    high_precision_coverage, high_precision_artifact = evaluate_and_write(50)

    assert low_precision_coverage == Decimal("0.6666666667")
    assert high_precision_coverage == Decimal("0.6666666667")
    assert json.loads(low_precision_artifact)["metrics"]["coverage"] == "0.6666666667"
    assert low_precision_artifact == high_precision_artifact


def test_factor_evaluation_computes_turnover_independent_of_decimal_context(
    tmp_path: Path,
) -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")
    ddd = Asset("DDD")
    eee = Asset("EEE")
    previous = _factor_result((aaa, "5"), (bbb, "4"), (ccc, "3"), (ddd, "2"), (eee, "1"))
    current = _factor_result((aaa, "5"), (ddd, "4"), (eee, "3"), (bbb, "2"), (ccc, "1"))

    def evaluate_and_write(precision: int) -> tuple[Decimal | None, str]:
        with localcontext() as context:
            context.prec = precision
            evaluation = FactorEvaluation.evaluate(
                FactorEvaluationInput(
                    as_of=date(2026, 1, 3),
                    factor_name="momentum",
                    factor_version="1",
                    factor_result=current,
                    previous_factor_result=previous,
                    forward_returns={
                        aaa.symbol: Decimal("0.05"),
                        bbb.symbol: Decimal("0.02"),
                        ccc.symbol: Decimal("0.01"),
                        ddd.symbol: Decimal("0.04"),
                        eee.symbol: Decimal("0.03"),
                    },
                    bucket_count=2,
                )
            )
            path = FactorEvaluationArtifactWriter(tmp_path / f"turnover-{precision}").write(
                evaluation
            )
            return evaluation.metrics.turnover, path.read_text(encoding="utf-8")

    low_precision_turnover, low_precision_artifact = evaluate_and_write(5)
    high_precision_turnover, high_precision_artifact = evaluate_and_write(50)

    assert low_precision_turnover == Decimal("0.6666666667")
    assert high_precision_turnover == Decimal("0.6666666667")
    assert json.loads(low_precision_artifact)["metrics"]["turnover"] == "0.6666666667"
    assert low_precision_artifact == high_precision_artifact


def test_factor_evaluation_handles_non_constant_tied_ranks() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")

    evaluation = FactorEvaluation.evaluate(
        FactorEvaluationInput(
            as_of=date(2026, 1, 2),
            factor_name="tied_factor",
            factor_version="1",
            factor_result=_factor_result((aaa, "2"), (bbb, "2"), (ccc, "1")),
            forward_returns={
                aaa.symbol: Decimal("0.03"),
                bbb.symbol: Decimal("0.01"),
                ccc.symbol: Decimal("0.02"),
            },
            bucket_count=3,
        )
    )

    assert evaluation.metrics.rank_ic == Decimal("0")


def test_factor_evaluation_without_previous_snapshot_has_no_turnover() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")

    evaluation = FactorEvaluation.evaluate(
        FactorEvaluationInput(
            as_of=date(2026, 1, 2),
            factor_name="momentum",
            factor_version="1",
            factor_result=_factor_result((aaa, "2"), (bbb, "1")),
            forward_returns={aaa.symbol: Decimal("0.02"), bbb.symbol: Decimal("0.01")},
            bucket_count=2,
        )
    )

    assert evaluation.metrics.turnover is None


def test_factor_evaluation_requires_two_assets_with_forward_returns() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")

    with pytest.raises(ValueError, match="at least two scored assets with forward returns"):
        FactorEvaluation.evaluate(
            FactorEvaluationInput(
                as_of=date(2026, 1, 2),
                factor_name="momentum",
                factor_version="1",
                factor_result=_factor_result((aaa, "2"), (bbb, "1")),
                forward_returns={aaa.symbol: Decimal("0.02")},
                bucket_count=2,
            )
        )


def test_factor_evaluation_rejects_constant_factor_and_return_ranks() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")

    with pytest.raises(ValueError, match="rank IC is undefined for constant ranks"):
        FactorEvaluation.evaluate(
            FactorEvaluationInput(
                as_of=date(2026, 1, 2),
                factor_name="flat_factor",
                factor_version="1",
                factor_result=_factor_result((aaa, "1"), (bbb, "1"), (ccc, "1")),
                forward_returns={
                    aaa.symbol: Decimal("0.01"),
                    bbb.symbol: Decimal("0.01"),
                    ccc.symbol: Decimal("0.01"),
                },
                bucket_count=3,
            )
        )


def test_factor_evaluation_rejects_constant_factor_ranks_only() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")

    with pytest.raises(ValueError, match="rank IC is undefined for constant ranks"):
        FactorEvaluation.evaluate(
            FactorEvaluationInput(
                as_of=date(2026, 1, 2),
                factor_name="flat_factor",
                factor_version="1",
                factor_result=_factor_result((aaa, "1"), (bbb, "1"), (ccc, "1")),
                forward_returns={
                    aaa.symbol: Decimal("0.03"),
                    bbb.symbol: Decimal("0.02"),
                    ccc.symbol: Decimal("0.01"),
                },
                bucket_count=3,
            )
        )


def test_factor_evaluation_rejects_constant_return_ranks_only() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")

    with pytest.raises(ValueError, match="rank IC is undefined for constant ranks"):
        FactorEvaluation.evaluate(
            FactorEvaluationInput(
                as_of=date(2026, 1, 2),
                factor_name="momentum",
                factor_version="1",
                factor_result=_factor_result((aaa, "3"), (bbb, "2"), (ccc, "1")),
                forward_returns={
                    aaa.symbol: Decimal("0.01"),
                    bbb.symbol: Decimal("0.01"),
                    ccc.symbol: Decimal("0.01"),
                },
                bucket_count=3,
            )
        )


def test_factor_evaluation_artifact_is_stable_json(tmp_path: Path) -> None:
    writer = FactorEvaluationArtifactWriter(tmp_path)
    result = FactorEvaluationResult(
        as_of=date(2026, 1, 2),
        factor_name="momentum",
        factor_version="1",
        metrics=FactorEvaluationMetrics(
            rank_ic=Decimal("1"),
            long_short_spread=Decimal("0.05"),
            coverage=Decimal("1"),
            turnover=Decimal("0.5"),
            scored_count=3,
            return_count=3,
            missing_symbols=(),
        ),
    )

    left_path = writer.write(result)
    right_path = writer.write(result)
    payload = json.loads(left_path.read_text(encoding="utf-8"))

    assert left_path == right_path
    assert left_path.read_text(encoding="utf-8").endswith("\n")
    assert payload == {
        "as_of": "2026-01-02",
        "factor_name": "momentum",
        "factor_version": "1",
        "metrics": {
            "coverage": "1",
            "long_short_spread": "0.05",
            "missing_symbols": [],
            "rank_ic": "1",
            "return_count": 3,
            "scored_count": 3,
            "turnover": "0.5",
        },
    }
