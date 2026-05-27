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
    assert manifest.calendar == "CME"
    assert manifest.metrics_schema_id == "schema_v2"
    assert manifest.promotion_policy_id == "default_research_policy"
    assert manifest.required_artifacts == (
        "metrics",
        "data_quality",
        "reproducibility",
        "promotion_packet",
    )
    assert [candidate.candidate_id for candidate in manifest.candidates()] == [
        candidate.candidate_id for candidate in second.candidates()
    ]
    assert manifest.to_payload()["schema_version"] == 2


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


def _write_manifest_v2(tmp_path: Path, overrides: dict[str, object] | None = None) -> Path:
    payload: dict[str, object] = {
        "schema_version": 2,
        "run": {
            "id": "research-os-v2",
            "question": "Can a v2 manifest drive deterministic research evidence?",
            "owner": "research",
        },
        "strategy": {
            "id": "gc_si_momentum",
            "source_module": "examples.strategies.gc_si_momentum",
            "entrypoint": "GcSiMomentumStrategy",
            "default_config": "configs/strategies/gc_si_momentum.yaml",
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
        "metrics_schema": {"id": "schema_v2", "version": 2},
        "promotion_policy": {
            "id": "default_research_policy",
            "version": 1,
            "config": "configs/promotion/default.yaml",
        },
        "artifacts": {
            "required": ["metrics", "data_quality", "reproducibility", "promotion_packet"]
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
