from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research.factor_spec import FactorSpec, FactorSpecSourceRef
from qts.research.factor_spec_store import FactorSpecStore


def _spec(name: str = "momentum-carry") -> FactorSpec:
    return FactorSpec(
        name=name,
        hypothesis=f"Research whether {name} predicts forward returns.",
        inputs=("close", "contract_chain"),
        lookback="63d",
        universe="commodity_futures",
        rebalance="daily",
        expected_direction="higher_score_higher_expected_return",
        data_requirements=("historical bars", "contract chain metadata"),
        source_refs=(
            FactorSpecSourceRef(
                source="openalex",
                external_id=f"W-{name}",
                title=f"{name} paper",
                url=f"https://openalex.org/{name}",
                year=2026,
            ),
        ),
        candidate_tags=("momentum", "carry"),
        notes=("human review required", "not executable factor code"),
    )


def test_factor_spec_store_saves_deterministic_json(tmp_path: Path) -> None:
    store = FactorSpecStore(tmp_path)
    spec = _spec()

    path = store.save(spec)

    expected = json.dumps(spec.to_payload(), sort_keys=True, indent=2) + "\n"
    assert path == tmp_path / "factor-specs" / "momentum-carry.json"
    assert path.read_text(encoding="utf-8") == expected


def test_factor_spec_store_lists_specs_sorted_by_name(tmp_path: Path) -> None:
    store = FactorSpecStore(tmp_path)
    store.save(_spec("value"))
    store.save(_spec("carry"))
    store.save(_spec("momentum"))

    specs = store.list_specs()

    assert tuple(spec.name for spec in specs) == ("carry", "momentum", "value")


def test_factor_spec_store_load_round_trips_spec(tmp_path: Path) -> None:
    store = FactorSpecStore(tmp_path)
    spec = _spec("quality")
    store.save(spec)

    loaded = store.load("quality")

    assert loaded == spec


@pytest.mark.parametrize(
    "name",
    ["", " ", "foo/bar", "foo\\bar", "..", "foo..bar", "alpha.json"],
)
def test_factor_spec_store_rejects_path_like_names(tmp_path: Path, name: str) -> None:
    store = FactorSpecStore(tmp_path)

    with pytest.raises(ValueError):
        store.path_for(name)


def test_factor_spec_store_direct_import_is_available() -> None:
    from qts.research import FactorSpecStore as ExportedFactorSpecStore
    from qts.research.factor_spec_store import FactorSpecStore as ImportedFactorSpecStore

    assert ImportedFactorSpecStore is FactorSpecStore
    assert ExportedFactorSpecStore is FactorSpecStore
