from __future__ import annotations

from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from qts.research.manifest import ResearchManifest, ResearchManifestV2


def test_manifest_v2_accepts_complete_contract_and_stable_candidates(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(tmp_path)

    manifest = ResearchManifestV2.from_yaml(manifest_path)
    second = ResearchManifestV2.from_yaml(manifest_path)

    assert manifest.schema_version == 2
    assert manifest.run_id == "research-os-v2"
    assert manifest.owner == "research"
    assert manifest.run_created_at == "2026-05-27T00:00:00+00:00"
    assert manifest.calendar == "CME"
    assert manifest.strategy_hypothesis == "GC/SI momentum persists after costs."
    assert manifest.metrics_schema_id == "schema_v2"
    assert manifest.metrics_schema_path.name == "schema_v2.yaml"
    assert manifest.promotion_policy_id == "default_research_policy"
    assert manifest.required_artifacts == (
        "artifact_graph",
        "data_quality",
        "evidence_bundle",
        "metrics",
        "reproducibility",
    )
    assert [candidate.candidate_id for candidate in manifest.candidates()] == [
        candidate.candidate_id for candidate in second.candidates()
    ]
    assert manifest.to_payload()["schema_version"] == 2
    assert manifest.to_payload()["run"]["created_at"] == "2026-05-27T00:00:00+00:00"
    assert manifest.to_payload()["strategy"]["hypothesis"] == "GC/SI momentum persists after costs."
    assert manifest.to_payload()["metrics_schema"]["path"].endswith("schema_v2.yaml")


def test_manifest_v2_rejects_wrong_schema_version(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(tmp_path, {"schema_version": 1})

    with pytest.raises(ValueError, match="schema_version must be 2"):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v2_rejects_non_increasing_time_range(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(
        tmp_path,
        {"data": {"start": "2026-01-02T15:00:00Z", "end": "2026-01-02T15:00:00Z"}},
    )

    with pytest.raises(ValueError, match="data.start must be before data.end"):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v2_rejects_timezone_naive_dates(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(
        tmp_path,
        {"data": {"start": "2026-01-02T15:00:00", "end": "2026-01-02T16:00:00Z"}},
    )

    with pytest.raises(ValueError, match="data.start must be timezone-aware"):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v2_rejects_missing_calendar(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(tmp_path, {"data": {"calendar": ""}})

    with pytest.raises(ValueError, match="data.calendar is required"):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v2_rejects_non_v2_metrics_schema(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(tmp_path, {"metrics_schema": {"version": 1}})

    with pytest.raises(ValueError, match="metrics_schema.version must be 2"):
        ResearchManifestV2.from_yaml(manifest_path)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"run": {"created_at": ""}}, "run.created_at is required"),
        ({"run": {"created_at": "2026-05-27T00:00:00"}}, "run.created_at must be timezone-aware"),
        ({"strategy": {"hypothesis": ""}}, "strategy.hypothesis is required"),
        ({"metrics_schema": {"path": ""}}, "metrics_schema.path is required"),
    ),
)
def test_manifest_v2_rejects_missing_required_contract_fields(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    manifest_path = _write_manifest_v2(tmp_path, overrides)

    with pytest.raises(ValueError, match=message):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v2_rejects_missing_required_artifact(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(
        tmp_path,
        {
            "artifacts": {
                "required": ["metrics", "data_quality", "reproducibility", "artifact_graph"]
            }
        },
    )

    with pytest.raises(ValueError, match="artifacts.required missing required artifact"):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v2_rejects_missing_required_hash_group(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(
        tmp_path,
        {"reproducibility": {"required_hash_groups": ["dependency_hashes", "config_hashes"]}},
    )

    with pytest.raises(
        ValueError,
        match="reproducibility.required_hash_groups missing required group",
    ):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v2_rejects_unresolvable_strategy_entrypoint(tmp_path: Path) -> None:
    manifest_path = _write_manifest_v2(
        tmp_path,
        {"strategy": {"entrypoint": "MissingStrategy"}},
    )

    with pytest.raises(ValueError, match="strategy entrypoint is not resolvable"):
        ResearchManifestV2.from_yaml(manifest_path)


def test_manifest_v1_loader_remains_compatible() -> None:
    manifest = ResearchManifest.from_yaml("configs/research/backtest_gc_si_smoke.yaml")

    assert manifest.run_id == "gc-si-smoke-dry-run"
    assert manifest.to_payload()["run"]["id"] == "gc-si-smoke-dry-run"


def test_manifest_v2_is_public_package_export() -> None:
    import qts.research as research

    assert research.ResearchManifestV2 is ResearchManifestV2


def test_manifest_v2_canonical_config_fixture_loads() -> None:
    manifest = ResearchManifestV2.from_yaml("configs/research/manifests/gc_si_smoke_v2.yaml")

    assert manifest.schema_version == 2
    assert manifest.run_id == "gc-si-smoke-v2"
    assert manifest.required_artifacts == (
        "artifact_graph",
        "data_quality",
        "evidence_bundle",
        "metrics",
        "reproducibility",
    )


def _write_manifest_v2(tmp_path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload: dict[str, object] = {
        "schema_version": 2,
        "run": {
            "id": "research-os-v2",
            "question": "Can a v2 manifest drive deterministic research evidence?",
            "owner": "research",
            "created_at": "2026-05-27T00:00:00+00:00",
        },
        "strategy": {
            "id": "gc_si_momentum",
            "source_module": "examples.strategies.gc_si_momentum",
            "entrypoint": "GcSiMomentumStrategy",
            "default_config": "configs/strategies/gc_si_momentum.yaml",
            "hypothesis": "GC/SI momentum persists after costs.",
        },
        "data": {
            "dataset_id": "research_futures_gc_si_1m",
            "config": "configs/data/historical.local.yaml",
            "catalog": "research_futures",
            "roots": ["GC", "SI"],
            "timeframe": "1m",
            "start": "2010-06-06T22:00:00Z",
            "end": "2010-06-06T22:05:00Z",
            "calendar": "CME",
        },
        "metrics_schema": {
            "id": "schema_v2",
            "version": 2,
            "path": "configs/research/metrics/schema_v2.yaml",
        },
        "promotion_policy": {
            "id": "default_research_policy",
            "version": 1,
            "path": "configs/promotion/default.yaml",
        },
        "artifacts": {
            "required": [
                "artifact_graph",
                "data_quality",
                "evidence_bundle",
                "metrics",
                "reproducibility",
            ]
        },
        "reproducibility": {
            "require_clean_git": True,
            "required_hash_groups": ["dependency_hashes", "config_hashes", "data_hashes"],
        },
        "parameter_grid": {"short_window": [1, 2], "long_window": [3]},
        "output_root": str(tmp_path / "artifacts" / "research"),
        "splits": {
            "windows": [
                {
                    "name": "train",
                    "role": "in_sample",
                    "start": "2010-06-06",
                    "end": "2010-06-07",
                },
                {
                    "name": "oos",
                    "role": "out_of_sample",
                    "start": "2010-06-07",
                    "end": "2010-06-08",
                },
            ]
        },
    }
    if overrides:
        _merge(payload, overrides)
    path = tmp_path / "manifest_v2.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def _merge(target: dict[str, object], overrides: dict[str, object]) -> None:
    for key, value in overrides.items():
        existing = target.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            _merge(existing, value)
        else:
            target[key] = value
