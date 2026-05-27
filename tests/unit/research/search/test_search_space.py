"""Phase 3 search-space contract tests."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from qts.research.search import (
    CandidateGenerator,
    SearchConstraint,
    SearchParameter,
    SearchSpaceSpec,
)


def test_finite_grid_generates_deterministic_candidates_and_space_hash(tmp_path: Path) -> None:
    spec = SearchSpaceSpec(
        parameters=(
            SearchParameter.categorical("entry_signal", ("breakout", "pullback")),
            SearchParameter.int_range("lookback", minimum=5, maximum=10, step=5),
            SearchParameter.boolean("use_trailing_stop"),
        )
    )
    same_spec = SearchSpaceSpec(
        parameters=(
            SearchParameter.categorical("entry_signal", ("breakout", "pullback")),
            SearchParameter.int_range("lookback", minimum=5, maximum=10, step=5),
            SearchParameter.boolean("use_trailing_stop"),
        )
    )

    candidates = CandidateGenerator(spec).grid()

    assert spec.candidate_space_hash == same_spec.candidate_space_hash
    assert [candidate.parameters for candidate in candidates] == [
        {"entry_signal": "breakout", "lookback": 5, "use_trailing_stop": False},
        {"entry_signal": "breakout", "lookback": 5, "use_trailing_stop": True},
        {"entry_signal": "breakout", "lookback": 10, "use_trailing_stop": False},
        {"entry_signal": "breakout", "lookback": 10, "use_trailing_stop": True},
        {"entry_signal": "pullback", "lookback": 5, "use_trailing_stop": False},
        {"entry_signal": "pullback", "lookback": 5, "use_trailing_stop": True},
        {"entry_signal": "pullback", "lookback": 10, "use_trailing_stop": False},
        {"entry_signal": "pullback", "lookback": 10, "use_trailing_stop": True},
    ]
    assert {candidate.candidate_space_hash for candidate in candidates} == {
        spec.candidate_space_hash
    }
    assert len({candidate.candidate_id for candidate in candidates}) == len(candidates)

    output_path = tmp_path / "candidate_parameters.jsonl"
    CandidateGenerator(spec).write_jsonl(output_path, candidates)
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["candidate_space_hash"] == spec.candidate_space_hash
    assert rows[0]["parameters"]["entry_signal"] == "breakout"


def test_random_generation_is_deterministic_under_seed() -> None:
    spec = SearchSpaceSpec(
        parameters=(
            SearchParameter.int_range("lookback", minimum=2, maximum=8),
            SearchParameter.float_range("threshold", minimum="0.1", maximum="0.9"),
            SearchParameter.log_float_range("risk", minimum="0.001", maximum="0.1"),
        )
    )

    first = CandidateGenerator(spec).random(seed=17, budget=5)
    second = CandidateGenerator(spec).random(seed=17, budget=5)
    different_seed = CandidateGenerator(spec).random(seed=18, budget=5)

    assert [candidate.parameters for candidate in first] == [
        candidate.parameters for candidate in second
    ]
    assert [candidate.candidate_id for candidate in first] == [
        candidate.candidate_id for candidate in second
    ]
    assert [candidate.parameters for candidate in first] != [
        candidate.parameters for candidate in different_seed
    ]
    assert all(
        2 <= candidate.parameters["lookback"] <= 8
        and Decimal("0.1") <= candidate.parameters["threshold"] <= Decimal("0.9")
        and Decimal("0.001") <= candidate.parameters["risk"] <= Decimal("0.1")
        for candidate in first
    )


def test_conditionals_remove_inactive_parameters_without_duplicate_candidates() -> None:
    spec = SearchSpaceSpec(
        parameters=(
            SearchParameter.boolean("use_stop"),
            SearchParameter.int_range("stop_ticks", minimum=4, maximum=8, step=4),
        ),
        constraints=(
            SearchConstraint.conditional(
                parameter="stop_ticks",
                when={"use_stop": True},
            ),
        ),
    )

    candidates = CandidateGenerator(spec).grid()

    assert [candidate.parameters for candidate in candidates] == [
        {"use_stop": False},
        {"stop_ticks": 4, "use_stop": True},
        {"stop_ticks": 8, "use_stop": True},
    ]


def test_forbidden_combinations_are_excluded() -> None:
    spec = SearchSpaceSpec(
        parameters=(
            SearchParameter.categorical("side", ("long", "short")),
            SearchParameter.categorical("asset_bucket", ("liquid", "thin")),
        ),
        constraints=(
            SearchConstraint.forbidden_combination(
                values={"side": "short", "asset_bucket": "thin"},
            ),
        ),
    )

    candidates = CandidateGenerator(spec).grid()

    assert [candidate.parameters for candidate in candidates] == [
        {"asset_bucket": "liquid", "side": "long"},
        {"asset_bucket": "thin", "side": "long"},
        {"asset_bucket": "liquid", "side": "short"},
    ]


def test_unbounded_space_is_rejected_without_budget() -> None:
    spec = SearchSpaceSpec(
        parameters=(SearchParameter.float_range("threshold", minimum="0.1", maximum="0.9"),)
    )

    with pytest.raises(ValueError, match="unbounded search space requires budget"):
        CandidateGenerator(spec).grid()

    assert len(CandidateGenerator(spec).random(seed=23, budget=3)) == 3


def test_invalid_search_space_definitions_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate search parameter"):
        SearchSpaceSpec(
            parameters=(
                SearchParameter.boolean("enabled"),
                SearchParameter.categorical("enabled", ("yes", "no")),
            )
        )

    with pytest.raises(ValueError, match="unknown conditional parameter"):
        SearchSpaceSpec(
            parameters=(SearchParameter.boolean("enabled"),),
            constraints=(SearchConstraint.conditional("missing", when={"enabled": True}),),
        )
