from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.research import (
    ExperimentManifestConfig,
    ExperimentManifestWriter,
    FactorSpecDrafter,
    ResearchSession,
    ResearchSessionConfig,
)
from qts.research.factor_discovery import FactorIdea


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
