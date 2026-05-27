from __future__ import annotations

import json

from qts.research.factory import (
    FactorDefinition,
    FactorInput,
    FactorLabelPolicy,
    FactorTransform,
)


def _valid_factor() -> FactorDefinition:
    return FactorDefinition(
        factor_id="gc_si_spread_zscore_v1",
        family="spread_zscore",
        inputs=(
            FactorInput(root="GC", field="close"),
            FactorInput(root="SI", field="close"),
        ),
        transforms=(
            FactorTransform(transform_type="ratio"),
            FactorTransform(transform_type="rolling_zscore", parameters={"lookback": 240}),
        ),
        label_policy=FactorLabelPolicy(
            horizon_bars=60,
            visible_after="close",
            no_lookahead=True,
        ),
    )


def test_valid_factor_definition_is_accepted_and_hash_is_deterministic() -> None:
    factor = _valid_factor()

    result = factor.validate(allowed_roots=("GC", "SI"))

    assert result.accepted is True
    assert result.errors == ()
    assert factor.factor_hash == FactorDefinition.from_payload(factor.to_payload()).factor_hash
    assert json.dumps(factor.to_payload(), sort_keys=True)


def test_factor_definition_exports_artifact_graph_node() -> None:
    factor = _valid_factor()

    node = factor.to_artifact_node()

    assert node.node_id == "gc_si_spread_zscore_v1"
    assert node.node_type == "factor_definition"
    assert node.payload_hash == factor.factor_hash
    assert node.metadata["family"] == "spread_zscore"


def test_factor_definition_rejects_unknown_input_root() -> None:
    factor = FactorDefinition(
        factor_id="unknown_root_v1",
        family="momentum",
        inputs=(FactorInput(root="HG", field="close"),),
        transforms=(FactorTransform(transform_type="returns", parameters={"lookback": 30}),),
        label_policy=FactorLabelPolicy(
            horizon_bars=20,
            visible_after="close",
            no_lookahead=True,
        ),
    )

    result = factor.validate(allowed_roots=("GC", "SI"))

    assert result.accepted is False
    assert "unknown input root: HG" in result.errors


def test_factor_definition_rejects_future_looking_transform() -> None:
    factor = FactorDefinition(
        factor_id="lookahead_v1",
        family="momentum",
        inputs=(FactorInput(root="GC", field="close"),),
        transforms=(FactorTransform(transform_type="forward_return", parameters={"horizon": 5}),),
        label_policy=FactorLabelPolicy(
            horizon_bars=20,
            visible_after="close",
            no_lookahead=True,
        ),
    )

    result = factor.validate(allowed_roots=("GC",))

    assert result.accepted is False
    assert "transform forward_return references future data" in result.errors


def test_factor_definition_rejects_missing_label_policy_and_disabled_no_lookahead() -> None:
    missing_policy = FactorDefinition(
        factor_id="missing_label_v1",
        family="momentum",
        inputs=(FactorInput(root="GC", field="close"),),
        transforms=(FactorTransform(transform_type="returns", parameters={"lookback": 30}),),
        label_policy=None,
    )
    disabled_policy = FactorDefinition(
        factor_id="disabled_lookahead_v1",
        family="momentum",
        inputs=(FactorInput(root="GC", field="close"),),
        transforms=(FactorTransform(transform_type="returns", parameters={"lookback": 30}),),
        label_policy=FactorLabelPolicy(
            horizon_bars=20,
            visible_after="close",
            no_lookahead=False,
        ),
    )

    assert missing_policy.validate(allowed_roots=("GC",)).errors == ("label_policy is required",)
    assert disabled_policy.validate(allowed_roots=("GC",)).errors == (
        "label_policy.no_lookahead must be true",
    )


def test_factor_definition_rejects_unknown_family_and_invalid_transform_parameters() -> None:
    factor = FactorDefinition(
        factor_id="bad_transform_v1",
        family="macro",
        inputs=(FactorInput(root="GC", field="close"),),
        transforms=(FactorTransform(transform_type="rolling_zscore", parameters={"lookback": 0}),),
        label_policy=FactorLabelPolicy(
            horizon_bars=20,
            visible_after="close",
            no_lookahead=True,
        ),
    )

    result = factor.validate(allowed_roots=("GC",))

    assert result.accepted is False
    assert "unsupported factor family: macro" in result.errors
    assert "transform rolling_zscore parameter lookback must be positive" in result.errors
