from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from qts.research import (
    ExperimentManifestConfig,
    ExperimentManifestWriter,
    FactorSpecDrafter,
    ResearchSession,
    ResearchSessionConfig,
)
from qts.research.factor_discovery import (
    FactorDiscovery,
    FactorDiscoveryQuery,
    FactorIdea,
    FactorIdeaStore,
)
from qts.research.optimizer import WalkForwardPlan, WalkForwardSplit


class _CountingSource:
    name = "fixture"

    def __init__(self, ideas: tuple[FactorIdea, ...]) -> None:
        self.calls = 0
        self._ideas = ideas

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        self.calls += 1
        return self._ideas


def _write_research_config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "research.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _minimal_research_yaml(tmp_path: Path) -> str:
    data_config = tmp_path / "historical.local.yaml"
    data_config.write_text("historical_data: {}\n", encoding="utf-8")
    backtest_config = tmp_path / "backtest.yaml"
    backtest_config.write_text("mode: backtest\n", encoding="utf-8")
    return f"""
data:
  config: {data_config.name}
  catalog: research_futures
  roots: [GC]
  timeframe: 1m
backtest_config: {backtest_config.name}
store: research-store
output_root: backtests
objective_metric: total_return
"""


def test_research_session_config_loads_paths_relative_to_config_file(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))

    config = ResearchSessionConfig.from_yaml(config_path)

    assert config.research_config_path == config_path
    assert config.data_config_path == tmp_path / "historical.local.yaml"
    assert config.backtest_config_path == tmp_path / "backtest.yaml"
    assert config.store_root == tmp_path / "research-store"
    assert config.output_root == tmp_path / "backtests"
    assert config.catalog_name == "research_futures"
    assert config.roots == ("GC",)
    assert config.timeframe == "1m"
    assert config.objective_metric == "total_return"


def test_research_session_config_loads_discovery_defaults(tmp_path: Path) -> None:
    config_path = _write_research_config(
        tmp_path,
        _minimal_research_yaml(tmp_path)
        + """
discovery:
  sources: [openalex, crossref]
  max_results: 7
""",
    )

    config = ResearchSessionConfig.from_yaml(config_path)

    assert config.discovery_sources == ("openalex", "crossref")
    assert config.discovery_max_results == 7


def test_research_session_config_rejects_empty_roots(tmp_path: Path) -> None:
    data_config = tmp_path / "historical.local.yaml"
    data_config.write_text("historical_data: {}\n", encoding="utf-8")
    backtest_config = tmp_path / "backtest.yaml"
    backtest_config.write_text("mode: backtest\n", encoding="utf-8")
    config_path = _write_research_config(
        tmp_path,
        f"""
data:
  config: {data_config}
  catalog: research_futures
  roots: []
  timeframe: 1m
backtest_config: {backtest_config}
""",
    )

    with pytest.raises(ValueError, match="data.roots must not be empty"):
        ResearchSessionConfig.from_yaml(config_path)


def test_research_session_config_rejects_missing_backtest_config(tmp_path: Path) -> None:
    config_path = _write_research_config(
        tmp_path,
        """
data:
  config: historical.local.yaml
  catalog: research_futures
  roots: [GC]
  timeframe: 1m
backtest_config: missing-backtest.yaml
""",
    )

    with pytest.raises(FileNotFoundError, match="backtest config not found"):
        ResearchSessionConfig.from_yaml(config_path)


def test_research_session_from_yaml_exposes_book_and_store(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))

    session = ResearchSession.from_yaml(config_path)

    assert session.config.research_book_config().catalog_name == "research_futures"
    assert session.store.index_path == tmp_path / "research-store" / "experiments.jsonl"


def test_research_session_from_yaml_accepts_string_paths(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))

    session = ResearchSession.from_yaml(str(config_path))

    assert session.config.research_config_path == config_path


def test_research_session_parameter_grid_rejects_empty_values(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)

    with pytest.raises(ValueError, match="parameter values must not be empty"):
        session.parameter_grid({"lookback": []})


def test_research_session_run_backtest_uses_override_config_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    override_config = tmp_path / "production-baseline.yaml"
    override_config.write_text("mode: backtest\n", encoding="utf-8")
    calls: list[dict[str, Any]] = []

    class FakeEngine:
        def run_streaming(self, output_dir: Path, *, compact_events: bool) -> object:
            calls.append({"compact_events": compact_events, "output_dir": output_dir})
            return SimpleNamespace(manifest_path=tmp_path / "manifest.json")

    class FakePipeline:
        def __init__(self, path: Path) -> None:
            self._path = path

        @classmethod
        def from_yaml(cls, path: Path) -> FakePipeline:
            calls.append({"from_yaml": path})
            return cls(path)

        def with_strategy_params(self, params: dict[str, object]) -> FakePipeline:
            calls.append({"strategy_params": params})
            return self

        def build_engine(self) -> tuple[FakeEngine, object]:
            calls.append({"build_engine": self._path})
            return FakeEngine(), object()

    monkeypatch.setattr("qts.research.session.BacktestPipeline", FakePipeline)

    session.run_backtest(
        backtest_config_path=override_config,
        strategy_params={"quantity": "4"},
        output_dir=tmp_path / "baseline",
    )

    assert calls == [
        {"from_yaml": override_config},
        {"strategy_params": {"quantity": "4"}},
        {"build_engine": override_config},
        {"compact_events": True, "output_dir": tmp_path / "baseline"},
    ]


def test_research_session_run_backtest_delegates_date_range(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    calls: list[dict[str, Any]] = []

    class FakeEngine:
        def run_streaming(self, output_dir: Path, *, compact_events: bool) -> object:
            calls.append({"compact_events": compact_events, "output_dir": output_dir})
            return SimpleNamespace(manifest_path=tmp_path / "manifest.json")

    class FakePipeline:
        @classmethod
        def from_yaml(cls, path: Path) -> FakePipeline:
            calls.append({"from_yaml": path})
            return cls()

        def with_date_range(self, *, start: datetime, end: datetime) -> FakePipeline:
            calls.append({"date_range": (start, end)})
            return self

        def build_engine(self) -> tuple[FakeEngine, object]:
            calls.append({"build_engine": True})
            return FakeEngine(), object()

    monkeypatch.setattr("qts.research.session.BacktestPipeline", FakePipeline)
    start = datetime(2022, 1, 1, tzinfo=UTC)
    end = datetime(2025, 1, 1, tzinfo=UTC)

    session.run_backtest(start=start, end=end)

    assert calls == [
        {"from_yaml": session.config.backtest_config_path},
        {"date_range": (start, end)},
        {"build_engine": True},
        {"compact_events": True, "output_dir": session.config.output_root / "single-run"},
    ]


def test_research_session_run_backtest_rejects_partial_date_range(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)

    with pytest.raises(ValueError, match="start and end must be provided together"):
        session.run_backtest(start=datetime(2022, 1, 1, tzinfo=UTC))


def test_research_session_delegates_walk_forward_validation_to_backtest_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    calls: list[dict[str, Any]] = []

    class FakeRunner:
        def run(self, job: Any) -> tuple[object, ...]:
            calls.append(
                {
                    "base_config_path": job.base_config_path,
                    "candidate_parameters": job.candidate_parameters,
                    "objective_metric": job.objective_metric,
                    "output_root": job.output_root,
                    "plan": job.plan,
                }
            )
            manifest_path = tmp_path / "wf-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "manifest_hash": "wf",
                        "metrics": {"sharpe_ratio": "1", "total_trades": "3"},
                    }
                ),
                encoding="utf-8",
            )
            return (
                SimpleNamespace(
                    split_name="split-001",
                    phase="test",
                    start=date(2026, 4, 1),
                    end=date(2026, 5, 1),
                    result=SimpleNamespace(
                        parameters={"alpha": "1"},
                        manifest_path=manifest_path,
                        manifest_hash="wf",
                        objective_value=Decimal("1"),
                    ),
                ),
            )

    monkeypatch.setattr("qts.research.session.BacktestWalkForwardValidationRunner", FakeRunner)
    plan = WalkForwardPlan(
        (
            WalkForwardSplit(
                name="split-001",
                train_start=date(2026, 1, 1),
                train_end=date(2026, 3, 1),
                test_start=date(2026, 4, 1),
                test_end=date(2026, 5, 1),
            ),
        )
    )

    summary = session.validate_optimizer_walk_forward(
        candidate_parameters=({"alpha": "1"},),
        objective_metric="sharpe_ratio",
        output_root=tmp_path / "wf-output",
        plan=plan,
    )

    assert calls == [
        {
            "base_config_path": tmp_path / "backtest.yaml",
            "candidate_parameters": ({"alpha": "1"},),
            "objective_metric": "sharpe_ratio",
            "output_root": tmp_path / "wf-output",
            "plan": plan,
        }
    ]
    assert summary.to_payload()["run_count"] == 1


def test_research_session_delegates_failure_window_veto_to_backtest_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qts.research.optimizer import FailureWindow, MetricConstraint

    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    calls: list[dict[str, Any]] = []

    class FakeRunner:
        def run(self, job: Any) -> tuple[object, ...]:
            calls.append(
                {
                    "base_config_path": job.base_config_path,
                    "candidate_parameters": job.candidate_parameters,
                    "objective_metric": job.objective_metric,
                    "output_root": job.output_root,
                    "report_only_windows": job.report_only_windows,
                    "windows": job.windows,
                }
            )
            return ()

    class FakeSummary:
        @classmethod
        def from_results(
            cls,
            results: object,
            *,
            constraints: object,
            capital_metric_config: object = None,
        ) -> object:
            calls.append(
                {
                    "capital_metric_config": capital_metric_config,
                    "constraints": constraints,
                    "results": results,
                }
            )
            return cls()

        def to_payload(self) -> dict[str, object]:
            return {"decision": {"accepted": True, "reasons": ()}}

    monkeypatch.setattr("qts.research.session.FailureWindowVetoRunner", FakeRunner)
    monkeypatch.setattr("qts.research.session.FailureWindowVetoSummary", FakeSummary)
    window = FailureWindow("failure-2024", date(2024, 1, 1), date(2025, 1, 1))
    report_window = FailureWindow(
        "report-2025-2026",
        date(2025, 1, 1),
        date(2026, 4, 10),
        report_only=True,
    )
    constraint = MetricConstraint("pnl_usd", ">", Decimal("0"))

    summary = session.validate_optimizer_failure_window_veto(
        candidate_parameters=({"alpha": "1"},),
        windows=(window,),
        report_only_windows=(report_window,),
        constraints=(constraint,),
        capital_metric_config={"margin_proxy": "12000"},
        objective_metric="sharpe_ratio",
        output_root=tmp_path / "failure-veto",
    )

    assert summary.to_payload()["decision"]["accepted"] is True
    assert calls == [
        {
            "base_config_path": tmp_path / "backtest.yaml",
            "candidate_parameters": ({"alpha": "1"},),
            "objective_metric": "sharpe_ratio",
            "output_root": tmp_path / "failure-veto",
            "report_only_windows": (report_window,),
            "windows": (window,),
        },
        {
            "capital_metric_config": {"margin_proxy": "12000"},
            "constraints": (constraint,),
            "results": (),
        },
    ]


def _write_manifest(
    tmp_path: Path,
    *,
    experiment_id: str,
    metric: str,
    value: str,
) -> Path:
    artifact_path = tmp_path / f"{experiment_id}.json"
    artifact_path.write_text(json.dumps({"metric": value}), encoding="utf-8")
    return (
        ExperimentManifestWriter(tmp_path / "manifests")
        .write_manifest(
            ExperimentManifestConfig(
                experiment_id=experiment_id,
                strategy_name="optimizer",
                strategy_version="1",
                factor_versions={},
                dataset_ids=["fixture"],
                config={"metric": metric},
                artifact_paths=(artifact_path,),
                metrics={metric: value},
            )
        )
        .manifest_path
    )


def test_research_session_records_lists_and_compares_runs(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    weak = _write_manifest(tmp_path, experiment_id="weak", metric="sharpe_ratio", value="0.5")
    strong = _write_manifest(tmp_path, experiment_id="strong", metric="sharpe_ratio", value="1.2")

    session.record_manifest(weak, recorded_at=datetime(2026, 5, 19, tzinfo=UTC))
    session.record_manifest(strong, recorded_at=datetime(2026, 5, 20, tzinfo=UTC))

    assert [record.experiment_id for record in session.list_runs()] == ["strong", "weak"]
    assert [record.experiment_id for record in session.compare_runs("sharpe_ratio")] == [
        "strong",
        "weak",
    ]
    assert session.compare_runs("missing_metric") == ()


def test_research_session_compare_frame_returns_metric_table(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    manifest = _write_manifest(
        tmp_path,
        experiment_id="exp-001",
        metric="total_return",
        value="0.10",
    )
    session.record_manifest(manifest, recorded_at=datetime(2026, 5, 20, tzinfo=UTC))

    frame = session.compare_frame("total_return")

    assert list(frame["experiment_id"]) == ["exp-001"]
    assert list(frame["metric_value"]) == [Decimal("0.10")]


def _factor_idea() -> FactorIdea:
    return FactorIdea(
        idea_id="openalex:W123",
        source="openalex",
        external_id="W123",
        title="Momentum Carry in Futures",
        abstract="A carry and momentum factor.",
        url="https://openalex.org/W123",
        year=2026,
        authors=("Researcher",),
        citation_count=10,
    )


def test_research_session_saves_lists_and_loads_factor_specs(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    spec = FactorSpecDrafter().draft(_factor_idea())

    path = session.save_factor_spec(spec)
    loaded = session.load_factor_spec(spec.name)

    assert path == tmp_path / "research-store" / "factor-specs" / f"{spec.name}.json"
    assert session.list_factor_specs() == (spec,)
    assert loaded == spec


def test_research_session_start_experiment_records_manifest(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text(json.dumps({"sharpe_ratio": "1.2"}), encoding="utf-8")

    with session.start_experiment(
        "exp-001",
        strategy_name="research_strategy",
        strategy_version="2",
    ) as recorder:
        recorder.log_params({"lookback": 20})
        recorder.log_metric("sharpe_ratio", "1.2")
        recorder.log_factor_version("momentum", "1")
        recorder.log_dataset_id("fixture-bars")
        recorder.log_artifact(artifact_path)

    records = session.list_runs()
    assert [record.experiment_id for record in records] == ["exp-001"]
    assert records[0].strategy_name == "research_strategy"
    assert records[0].strategy_version == "2"
    assert records[0].factor_versions == {"momentum": "1"}
    assert records[0].dataset_ids == ("fixture-bars",)
    assert records[0].metrics == {"sharpe_ratio": "1.2"}


def test_research_session_find_factor_candidates_saves_specs(tmp_path: Path) -> None:
    config_path = _write_research_config(
        tmp_path,
        _minimal_research_yaml(tmp_path)
        + """
discovery:
  sources: [fixture]
  max_results: 1
""",
    )
    source = _CountingSource((_factor_idea(),))
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": source},
    )
    base_session = ResearchSession.from_yaml(config_path)
    session = ResearchSession(base_session.config, discovery=discovery)

    batch = session.find_factor_candidates("commodity futures alpha")

    assert source.calls == 1
    assert [spec.name for spec in batch.specs] == ["momentum-carry-in-futures"]
    assert session.load_factor_spec("momentum-carry-in-futures").review_status == "draft"
    assert list(batch.to_pandas()["spec_name"]) == ["momentum-carry-in-futures"]


def test_research_session_review_factor_spec_records_decision(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    spec = FactorSpecDrafter().draft(_factor_idea())
    session.save_factor_spec(spec)

    review = session.review_factor_spec(
        spec.name,
        decision="accepted",
        reviewer="researcher@example.com",
        notes=("source reviewed",),
        reviewed_at=datetime(2026, 5, 20, 13, 0, tzinfo=UTC),
    )

    assert review.spec_name == spec.name
    assert review.decision == "accepted"
    assert session.load_factor_spec(spec.name).review_status == "accepted"
    assert session.list_factor_reviews(decision="accepted") == (review,)
    assert session.list_factor_specs_by_status("accepted")[0].name == spec.name


def test_research_session_review_queue_frame_filters_drafts(tmp_path: Path) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    draft = FactorSpecDrafter().draft(_factor_idea())
    accepted = FactorSpecDrafter().draft(
        FactorIdea(
            idea_id="openalex:W456",
            source="openalex",
            external_id="W456",
            title="Volatility Timing in Futures",
            abstract="A volatility factor.",
            url="https://openalex.org/W456",
            year=2026,
            authors=("Researcher",),
            citation_count=10,
        )
    )
    session.save_factor_specs((draft, accepted))
    session.review_factor_spec(
        accepted.name,
        decision="accepted",
        reviewer="researcher@example.com",
        reviewed_at=datetime(2026, 5, 20, 13, 0, tzinfo=UTC),
    )

    frame = session.review_queue_frame()

    assert list(frame["spec_name"]) == [draft.name]
    assert list(frame["review_status"]) == ["draft"]


def test_research_session_candidate_public_exports_are_available() -> None:
    from qts.research import (
        FactorCandidate,
        FactorCandidateBatch,
        FactorCandidateWorkflow,
        FactorSpecReview,
    )

    assert FactorCandidate.__name__ == "FactorCandidate"
    assert FactorCandidateBatch.__name__ == "FactorCandidateBatch"
    assert FactorCandidateWorkflow.__name__ == "FactorCandidateWorkflow"
    assert FactorSpecReview.__name__ == "FactorSpecReview"


def test_research_session_evaluate_factor_generates_artifacts_from_mixed_input_types(
    tmp_path: Path,
) -> None:
    config_path = _write_research_config(tmp_path, _minimal_research_yaml(tmp_path))
    session = ResearchSession.from_yaml(config_path)
    score_day_1 = tmp_path / "scores_2026_01_02.csv"
    score_day_1.write_text(
        "\n".join(
            [
                "symbol,value",
                "AAPL,0.9",
                "MSFT,0.7",
                "NFLX,0.1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    returns_day_1 = tmp_path / "returns_2026_01_02.csv"
    returns_day_1.write_text(
        "\n".join(
            [
                "symbol,forward_return",
                "AAPL,0.04",
                "MSFT,0.01",
                "NFLX,0.00",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    score_day_2 = tmp_path / "scores_2026_01_03.json"
    score_day_2.write_text(
        json.dumps({"AAPL": 0.4, "MSFT": 0.9, "NFLX": 0.6}, sort_keys=True),
        encoding="utf-8",
    )
    returns_day_2 = tmp_path / "returns_2026_01_03.json"
    returns_day_2.write_text(
        json.dumps({"AAPL": 0.01, "MSFT": -0.03, "NFLX": 0.05}, sort_keys=True),
        encoding="utf-8",
    )

    snapshots = (
        {
            "as_of": "2026-01-02",
            "factor_scores": score_day_1,
            "forward_returns": returns_day_1,
        },
        {
            "as_of": date(2026, 1, 3),
            "factor_scores": score_day_2,
            "forward_returns": returns_day_2,
        },
    )

    results = session.evaluate_factor(
        factor_name="momentum",
        factor_version="1",
        snapshots=snapshots,
        bucket_count=2,
        output_dir=tmp_path / "factor-evaluations",
    )

    assert len(results) == 2
    for snapshot in results:
        assert snapshot.artifact_path.exists()

    assert results[0].artifact_path.name == "2026-01-02-momentum-1.json"
    assert results[1].artifact_path.name == "2026-01-03-momentum-1.json"
    assert results[0].result.metrics.turnover is None
    assert results[1].result.metrics.turnover == Decimal("0.5")
    payload = json.loads(results[1].artifact_path.read_text(encoding="utf-8"))
    assert payload["as_of"] == "2026-01-03"
    assert payload["metrics"]["scored_count"] == 3
    assert payload["metrics"]["return_count"] == 3
