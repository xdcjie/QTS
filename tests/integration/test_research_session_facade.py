"""Integration tests for the notebook-friendly ResearchSession facade."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.research import HistoryRequest, ResearchSession
from qts.research.factor_discovery import (
    FactorDiscovery,
    FactorDiscoveryQuery,
    FactorIdea,
    FactorIdeaStore,
)
from qts.research.factor_evaluation import (
    FactorEvaluationArtifactWriter,
    FactorEvaluationMetrics,
    FactorEvaluationResult,
)

from tests.integration.test_optimizer_consumes_backtest_config import _write_fixtures


class _CountingSource:
    name = "fixture"

    def __init__(self, ideas: tuple[FactorIdea, ...]) -> None:
        self._ideas = ideas

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        return self._ideas


def _write_research_session_config(tmp_path: Path) -> Path:
    backtest_config, data_config = _write_fixtures(tmp_path)
    config_path = tmp_path / "research.yaml"
    config_path.write_text(
        f"""
data:
  config: {data_config}
  catalog: research
  roots: [EQUITY]
  timeframe: 1m
  instrument_ids:
    AAPL: EQUITY.US.NASDAQ.AAPL
backtest_config: {backtest_config}
store: research-store
output_root: research-runs
objective_metric: total_return
""",
        encoding="utf-8",
    )
    return config_path


def test_research_session_reads_history_through_research_book(tmp_path: Path) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))

    frame = session.history_frame(
        HistoryRequest(
            root="EQUITY",
            start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
            end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
            timeframe="1m",
        )
    )

    assert len(frame) == 5
    assert list(frame["instrument_id"]) == ["EQUITY.US.NASDAQ.AAPL"] * 5


def test_research_session_run_backtest_uses_shared_backtest_pipeline(tmp_path: Path) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))

    result = session.run_backtest(strategy_params={"quantity": "2"})

    assert result.manifest_path.exists()
    assert result.trading_bars == 5
    assert result.processed_bars == 5
    assert result.manifest_path.parent == tmp_path / "research-runs" / "single-run"


def test_research_session_optimize_uses_backtest_pipeline_runner(tmp_path: Path) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))

    results = session.optimize(
        parameters={
            "entry_bar": [1, 2],
            "quantity": ["1", "2"],
        }
    )

    assert len(results) == 4
    assert all(result.manifest_path.exists() for result in results)
    assert all(
        result.manifest_path.parent.parent == tmp_path / "research-runs" / "optimizer"
        for result in results
    )


def test_research_session_experiment_recorder_keeps_backtest_path_unchanged(
    tmp_path: Path,
) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    artifact_path = tmp_path / "evidence.json"
    artifact_path.write_text(json.dumps({"total_return": "0.10"}), encoding="utf-8")

    with session.start_experiment(
        "manual-research",
        strategy_name="manual",
        strategy_version="1",
    ) as recorder:
        recorder.log_metric("total_return", "0.10")
        recorder.log_dataset_id("fixture-bars")
        recorder.log_artifact(artifact_path)

    result = session.run_backtest(strategy_params={"quantity": "2"})

    assert [record.experiment_id for record in session.list_runs()] == ["manual-research"]
    assert result.manifest_path.exists()
    assert result.manifest_path.parent == tmp_path / "research-runs" / "single-run"


def test_research_session_candidate_workflow_keeps_backtest_path_unchanged(
    tmp_path: Path,
) -> None:
    base_session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={
            "fixture": _CountingSource(
                (
                    FactorIdea(
                        idea_id="fixture:momentum",
                        source="fixture",
                        external_id="momentum",
                        title="Momentum factor in equity bars",
                        abstract="A momentum signal for research review.",
                        url="https://example.test/momentum",
                        year=2026,
                        authors=("Researcher",),
                        citation_count=10,
                    ),
                )
            )
        },
    )
    session = ResearchSession(base_session.config, discovery=discovery)

    batch = session.find_factor_candidates(
        "equity momentum",
        sources=("fixture",),
        max_results=1,
    )
    session.review_factor_spec(
        batch.specs[0].name,
        decision="needs_work",
        reviewer="researcher@example.com",
    )
    result = session.run_backtest(strategy_params={"quantity": "2"})

    assert session.load_factor_spec(batch.specs[0].name).review_status == "needs_work"
    assert result.manifest_path.exists()
    assert result.manifest_path.parent == tmp_path / "research-runs" / "single-run"


def test_research_session_records_factor_tearsheet_without_changing_backtest_path(
    tmp_path: Path,
) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    evaluation_writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluations")
    first = evaluation_writer.write(
        FactorEvaluationResult(
            as_of=date(2026, 1, 2),
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal("0.1"),
                long_short_spread=Decimal("0.01"),
                coverage=Decimal("0.8"),
                turnover=None,
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )
    second = evaluation_writer.write(
        FactorEvaluationResult(
            as_of=date(2026, 1, 3),
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal("0.3"),
                long_short_spread=Decimal("0.03"),
                coverage=Decimal("0.9"),
                turnover=Decimal("0.25"),
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )

    record = session.record_factor_tearsheet(
        (second, first),
        experiment_id="momentum-tearsheet",
        strategy_name="manual-factor-review",
        strategy_version="1",
        dataset_ids=("fixture-bars",),
    )
    result = session.run_backtest(strategy_params={"quantity": "2"})

    payload = json.loads(record.manifest_path.read_text(encoding="utf-8"))
    artifact_path = Path(next(iter(payload["artifact_paths_by_hash"].values())))
    assert record.experiment_id == "momentum-tearsheet"
    assert record.metrics["mean_rank_ic"] == "0.2"
    assert record.metrics["snapshot_count"] == 2
    assert payload["artifact_hashes"].keys() == {"momentum-1-tearsheet.json"}
    assert (
        artifact_path.parent
        == tmp_path / "research-runs" / "experiments" / "momentum-tearsheet" / "artifacts"
    )
    assert session.factor_tearsheet_frame((first, second)).shape[0] == 2
    assert result.manifest_path.exists()
    assert result.manifest_path.parent == tmp_path / "research-runs" / "single-run"


def test_research_session_record_factor_tearsheet_rejects_path_like_experiment_id(
    tmp_path: Path,
) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    evaluation_writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluations")
    artifact_path = evaluation_writer.write(
        FactorEvaluationResult(
            as_of=date(2026, 1, 2),
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal("0.1"),
                long_short_spread=Decimal("0.01"),
                coverage=Decimal("0.8"),
                turnover=None,
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )

    with pytest.raises(ValueError, match="experiment_id must be filename-safe"):
        session.record_factor_tearsheet(
            (artifact_path,),
            experiment_id="../unsafe",
        )


def test_research_session_record_factor_tearsheet_hash_is_artifact_order_independent(
    tmp_path: Path,
) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    evaluation_writer = FactorEvaluationArtifactWriter(tmp_path / "factor-evaluations")
    first = evaluation_writer.write(
        FactorEvaluationResult(
            as_of=date(2026, 1, 2),
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal("0.1"),
                long_short_spread=Decimal("0.01"),
                coverage=Decimal("0.8"),
                turnover=None,
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )
    second = evaluation_writer.write(
        FactorEvaluationResult(
            as_of=date(2026, 1, 3),
            factor_name="momentum",
            factor_version="1",
            metrics=FactorEvaluationMetrics(
                rank_ic=Decimal("0.3"),
                long_short_spread=Decimal("0.03"),
                coverage=Decimal("0.9"),
                turnover=None,
                scored_count=3,
                return_count=3,
                missing_symbols=(),
            ),
        )
    )

    left = session.record_factor_tearsheet((first, second), experiment_id="left-order")
    right = session.record_factor_tearsheet((second, first), experiment_id="right-order")

    assert left.config_hash == right.config_hash
    assert left.artifact_hashes == right.artifact_hashes
