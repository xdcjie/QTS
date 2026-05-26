from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research.experiment_recorder import ResearchExperimentRecorderConfig
from qts.research.experiment_store import ExperimentStore
from qts.research.idea_registry import IdeaRegistry
from qts.research.idea_spec import IdeaSpec


def _store(tmp_path: Path) -> ExperimentStore:
    return ExperimentStore(tmp_path / "research-index")


def _recorder_config(tmp_path: Path) -> ResearchExperimentRecorderConfig:
    return ResearchExperimentRecorderConfig(
        experiment_id="exp-001",
        strategy_name="mean_reversion",
        strategy_version="2026.05",
        manifest_root=tmp_path / "artifacts" / "research",
        store=_store(tmp_path),
    )


def test_experiment_recorder_finalizes_manifest_and_store_record(tmp_path: Path) -> None:
    from qts.research.experiment_recorder import ResearchExperimentRecorder

    artifact_path = tmp_path / "equity_curve.csv"
    artifact_path.write_text("date,equity\n2026-01-02,100000\n", encoding="utf-8")
    recorder = ResearchExperimentRecorder(_recorder_config(tmp_path))

    recorder.log_params({"lookback": 20, "threshold": 0.75})
    recorder.log_params({"threshold": 0.8})
    recorder.log_metrics({"total_return": 0.12})
    recorder.log_metric("sharpe", 1.25)
    recorder.log_factor_version("momentum", "1.0.0")
    recorder.log_dataset_id("daily-bars-v3")
    recorder.log_dataset_id("daily-bars-v3")
    recorder.log_artifact(artifact_path)
    record = recorder.finalize(recorded_at=datetime(2026, 5, 20, 12, 30, tzinfo=UTC))

    expected_artifact_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"
    payload = json.loads(record.manifest_path.read_text(encoding="utf-8"))
    assert record.experiment_id == "exp-001"
    assert record.strategy_name == "mean_reversion"
    assert record.strategy_version == "2026.05"
    assert record.factor_versions == {"momentum": "1.0.0"}
    assert record.dataset_ids == ("daily-bars-v3",)
    assert record.metrics == {"total_return": 0.12, "sharpe": 1.25}
    assert record.recorded_at == datetime(2026, 5, 20, 12, 30, tzinfo=UTC)
    assert payload["artifact_hashes"] == {"equity_curve.csv": expected_artifact_hash}
    assert payload["artifact_paths_by_hash"] == {expected_artifact_hash: str(artifact_path)}
    assert _store(tmp_path).list_runs() == (record,)


def test_experiment_recorder_links_idea_and_records_trial(tmp_path: Path) -> None:
    from qts.research.experiment_recorder import ResearchExperimentRecorder

    idea_registry = IdeaRegistry(tmp_path / "ideas")
    idea_registry.save_idea(
        IdeaSpec(
            idea_id="idea-momentum",
            title="Momentum",
            hypothesis="Momentum persists after costs.",
            edge_type="momentum",
            source="fixture",
            created_at=datetime(2026, 5, 20, tzinfo=UTC),
        )
    )
    config = ResearchExperimentRecorderConfig(
        experiment_id="exp-idea",
        strategy_name="mean_reversion",
        strategy_version="2026.05",
        manifest_root=tmp_path / "artifacts" / "research",
        store=_store(tmp_path),
        idea_id="idea-momentum",
        idea_registry=idea_registry,
    )

    record = ResearchExperimentRecorder(config).finalize(
        recorded_at=datetime(2026, 5, 21, tzinfo=UTC)
    )
    payload = json.loads(record.manifest_path.read_text(encoding="utf-8"))

    assert payload["idea_id"] == "idea-momentum"
    assert record.idea_id == "idea-momentum"
    assert _store(tmp_path).list_runs()[0].idea_id == "idea-momentum"
    assert idea_registry.get("idea-momentum").trial_count == 1


def test_experiment_recorder_context_manager_finalizes_on_clean_exit(tmp_path: Path) -> None:
    from qts.research.experiment_recorder import ResearchExperimentRecorder

    with ResearchExperimentRecorder(_recorder_config(tmp_path)) as recorder:
        assert recorder is not None

    records = _store(tmp_path).list_runs()
    assert len(records) == 1
    assert records[0].experiment_id == "exp-001"
    assert records[0].factor_versions == {}
    assert records[0].dataset_ids == ()
    assert records[0].metrics == {}


def test_experiment_recorder_does_not_record_failed_context(tmp_path: Path) -> None:
    from qts.research.experiment_recorder import ResearchExperimentRecorder

    with pytest.raises(RuntimeError, match="research failed"):
        with ResearchExperimentRecorder(_recorder_config(tmp_path)):
            raise RuntimeError("research failed")

    assert _store(tmp_path).list_runs() == ()
    assert not (tmp_path / "artifacts" / "research" / "exp-001" / "manifest.json").exists()


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("experiment_id", ""),
        ("strategy_name", ""),
        ("strategy_version", " "),
    ],
)
def test_experiment_recorder_rejects_empty_required_identity(
    tmp_path: Path,
    field_name: str,
    value: str,
) -> None:
    from qts.research.experiment_recorder import ResearchExperimentRecorderConfig

    experiment_id = "exp-001"
    strategy_name = "mean_reversion"
    strategy_version = "2026.05"
    if field_name == "experiment_id":
        experiment_id = value
    if field_name == "strategy_name":
        strategy_name = value
    if field_name == "strategy_version":
        strategy_version = value

    with pytest.raises(ValueError, match=f"{field_name} is required"):
        ResearchExperimentRecorderConfig(
            experiment_id=experiment_id,
            strategy_name=strategy_name,
            strategy_version=strategy_version,
            manifest_root=tmp_path / "artifacts" / "research",
            store=_store(tmp_path),
        )


def test_experiment_recorder_direct_import_and_input_validation(tmp_path: Path) -> None:
    from qts.research import ResearchExperimentRecorder as ExportedResearchExperimentRecorder
    from qts.research import (
        ResearchExperimentRecorderConfig as ExportedResearchExperimentRecorderConfig,
    )
    from qts.research.experiment_recorder import (
        ResearchExperimentRecorder,
        ResearchExperimentRecorderConfig,
    )

    recorder = ResearchExperimentRecorder(_recorder_config(tmp_path))

    assert ResearchExperimentRecorder.__name__ == "ResearchExperimentRecorder"
    assert ResearchExperimentRecorderConfig.__name__ == "ResearchExperimentRecorderConfig"
    assert ExportedResearchExperimentRecorder is ResearchExperimentRecorder
    assert ExportedResearchExperimentRecorderConfig is ResearchExperimentRecorderConfig
    with pytest.raises(ValueError, match="metric name is required"):
        recorder.log_metric("", 1)
    with pytest.raises(ValueError, match="factor name is required"):
        recorder.log_factor_version("", "1")
    with pytest.raises(ValueError, match="factor version is required"):
        recorder.log_factor_version("momentum", "")
    with pytest.raises(ValueError, match="dataset_id is required"):
        recorder.log_dataset_id("")
    with pytest.raises(FileNotFoundError, match="experiment artifact not found"):
        recorder.log_artifact(tmp_path / "missing.csv")
