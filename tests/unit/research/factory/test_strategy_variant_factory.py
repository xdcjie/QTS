from __future__ import annotations

from qts.research.factory import (
    FactorDefinition,
    FactorInput,
    FactorLabelPolicy,
    FactorTransform,
    StrategyTemplate,
    StrategyVariantFactory,
)


def _factor() -> FactorDefinition:
    return FactorDefinition(
        factor_id="gc_momentum_v1",
        family="momentum",
        inputs=(FactorInput(root="GC", field="close"),),
        transforms=(FactorTransform(transform_type="returns", parameters={"lookback": 60}),),
        label_policy=FactorLabelPolicy(
            horizon_bars=30,
            visible_after="close",
            no_lookahead=True,
        ),
    )


def _template() -> StrategyTemplate:
    return StrategyTemplate(
        template_id="threshold_rebalance_v1",
        family="threshold_rebalance",
        factor_definition=_factor(),
        strategy_entrypoint="strategies.research.factor_threshold:FactorThresholdStrategy",
        allowed_imports=("qts.strategy_sdk", "qts.domain"),
        parameter_space={
            "entry_z": (1.0, 1.5),
            "exit_z": (0.0, 0.5),
            "target_percent": (0.1, 0.2),
        },
        risk_assumptions={
            "max_gross_exposure": 0.3,
            "max_drawdown": 0.15,
        },
        execution_assumptions={
            "slippage_bps": 1.5,
            "commission_bps": 0.2,
        },
    )


def test_strategy_variant_factory_creates_deterministic_variant_id_and_hash() -> None:
    factory = StrategyVariantFactory(template=_template())
    parameters = {"entry_z": 1.5, "exit_z": 0.5, "target_percent": 0.2}

    first = factory.create_variant(parameters, allowed_roots=("GC",))
    second = factory.create_variant(
        dict(reversed(tuple(parameters.items()))), allowed_roots=("GC",)
    )

    assert first.variant_id == second.variant_id
    assert first.variant_hash == second.variant_hash
    assert first.factor_hash == _factor().factor_hash
    assert first.to_manifest_patch()["strategy"]["id"] == first.variant_id


def test_strategy_variant_exports_manifest_patch_and_artifact_graph_node() -> None:
    variant = StrategyVariantFactory(template=_template()).create_variant(
        {"entry_z": 1.5, "exit_z": 0.5, "target_percent": 0.2},
        allowed_roots=("GC",),
    )

    node = variant.to_artifact_node()

    assert node.node_id == variant.variant_id
    assert node.node_type == "strategy_variant"
    assert node.payload_hash == variant.variant_hash
    assert node.metadata == {
        "factor_hash": variant.factor_hash,
        "factor_id": "gc_momentum_v1",
        "template_id": "threshold_rebalance_v1",
    }


def test_strategy_template_rejects_forbidden_imports() -> None:
    template = StrategyTemplate(
        template_id="runtime_leak_v1",
        family="threshold_rebalance",
        factor_definition=_factor(),
        strategy_entrypoint="strategies.research.factor_threshold:FactorThresholdStrategy",
        allowed_imports=("qts.strategy_sdk", "qts.runtime.actors"),
        parameter_space={"entry_z": (1.0,), "exit_z": (0.0,)},
        risk_assumptions={"max_gross_exposure": 0.3},
        execution_assumptions={"slippage_bps": 1.5},
    )

    result = template.validate(allowed_roots=("GC",))

    assert result.accepted is False
    assert "forbidden import: qts.runtime.actors" in result.errors


def test_strategy_template_rejects_unbounded_parameter_space_without_budget() -> None:
    template = StrategyTemplate(
        template_id="unbounded_v1",
        family="threshold_rebalance",
        factor_definition=_factor(),
        strategy_entrypoint="strategies.research.factor_threshold:FactorThresholdStrategy",
        allowed_imports=("qts.strategy_sdk",),
        parameter_space={
            "entry_z": {"type": "float_range", "min": 0.5, "max": 3.0},
        },
        risk_assumptions={"max_gross_exposure": 0.3},
        execution_assumptions={"slippage_bps": 1.5},
    )

    result = template.validate(allowed_roots=("GC",))

    assert result.accepted is False
    assert "parameter space must be finite or trial_budget must be positive" in result.errors


def test_strategy_template_accepts_budget_bounded_parameter_space() -> None:
    template = StrategyTemplate(
        template_id="budgeted_v1",
        family="threshold_rebalance",
        factor_definition=_factor(),
        strategy_entrypoint="strategies.research.factor_threshold:FactorThresholdStrategy",
        allowed_imports=("qts.strategy_sdk",),
        parameter_space={
            "entry_z": {"type": "float_range", "min": 0.5, "max": 3.0},
        },
        risk_assumptions={"max_gross_exposure": 0.3},
        execution_assumptions={"slippage_bps": 1.5},
        trial_budget=25,
    )

    result = template.validate(allowed_roots=("GC",))

    assert result.accepted is True


def test_strategy_template_rejects_missing_assumptions_and_dynamic_generation() -> None:
    template = StrategyTemplate(
        template_id="missing_assumptions_v1",
        family="threshold_rebalance",
        factor_definition=_factor(),
        strategy_entrypoint="strategies.research.factor_threshold:FactorThresholdStrategy",
        allowed_imports=("qts.strategy_sdk",),
        parameter_space={"entry_z": (1.0,), "exit_z": (0.0,)},
        risk_assumptions={},
        execution_assumptions={},
        template_kind="dynamic_code",
    )

    result = template.validate(allowed_roots=("GC",))

    assert result.accepted is False
    assert "risk_assumptions are required" in result.errors
    assert "execution_assumptions are required" in result.errors
    assert "dynamic code generation is forbidden" in result.errors
