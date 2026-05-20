from __future__ import annotations

import json
from datetime import UTC, datetime
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


def test_factor_spec_store_records_review_and_updates_spec_status(tmp_path: Path) -> None:
    store = FactorSpecStore(tmp_path)
    store.save(_spec("carry"))
    reviewed_at = datetime(2026, 5, 20, 12, 30, tzinfo=UTC)

    review = store.record_review(
        "carry",
        decision=" accepted ",
        reviewer=" researcher@example.com ",
        notes=("  passes offline evidence review ", "", "passes offline evidence review"),
        reviewed_at=reviewed_at,
    )

    assert review.spec_name == "carry"
    assert review.decision == "accepted"
    assert review.reviewer == "researcher@example.com"
    assert review.reviewed_at == reviewed_at
    assert review.notes == ("passes offline evidence review",)
    assert store.load("carry").review_status == "accepted"
    assert store.reviews_path == tmp_path / "factor-spec-reviews.jsonl"
    assert store.reviews_path.read_text(encoding="utf-8") == (
        json.dumps(review.to_payload(), sort_keys=True) + "\n"
    )


def test_factor_spec_store_lists_reviews_newest_first_and_filters_decision(
    tmp_path: Path,
) -> None:
    store = FactorSpecStore(tmp_path)
    store.save(_spec("alpha"))
    store.save(_spec("beta"))
    store.save(_spec("gamma"))
    first_time = datetime(2026, 5, 20, 9, 0, tzinfo=UTC)
    newest_time = datetime(2026, 5, 20, 10, 0, tzinfo=UTC)

    store.record_review("beta", decision="rejected", reviewer="reviewer", reviewed_at=newest_time)
    store.record_review("alpha", decision="accepted", reviewer="reviewer", reviewed_at=newest_time)
    store.record_review("gamma", decision="accepted", reviewer="reviewer", reviewed_at=first_time)

    assert tuple(review.spec_name for review in store.list_reviews()) == (
        "alpha",
        "beta",
        "gamma",
    )
    assert tuple(review.spec_name for review in store.list_reviews(decision="accepted")) == (
        "alpha",
        "gamma",
    )


def test_factor_spec_store_rejects_unknown_review_decision(tmp_path: Path) -> None:
    store = FactorSpecStore(tmp_path)
    store.save(_spec("carry"))

    with pytest.raises(ValueError, match="review decision"):
        store.record_review("carry", decision="promoted", reviewer="reviewer")

    with pytest.raises(ValueError, match="review decision"):
        store.list_reviews(decision="promoted")


def test_factor_spec_store_lists_specs_by_status(tmp_path: Path) -> None:
    store = FactorSpecStore(tmp_path)
    store.save(_spec("value"))
    store.save(_spec("carry"))
    store.save(_spec("momentum"))
    store.record_review("value", decision="needs_work", reviewer="reviewer")
    store.record_review("carry", decision="needs_work", reviewer="reviewer")
    store.record_review("momentum", decision="accepted", reviewer="reviewer")

    assert tuple(spec.name for spec in store.list_specs_by_status("needs_work")) == (
        "carry",
        "value",
    )
    assert tuple(spec.name for spec in store.list_specs_by_status("accepted")) == ("momentum",)

    with pytest.raises(ValueError, match="review decision"):
        store.list_specs_by_status("promoted")


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
