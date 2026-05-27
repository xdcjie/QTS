"""Research factory DSL and template contracts."""

from qts.research.factory.discovery_mapper import (
    FactorDefinitionDraft,
    FactorDefinitionDraftConstraints,
    FactorDiscoveryDraftMapper,
)
from qts.research.factory.factor_definition import (
    FactorDefinition,
    FactorDefinitionValidationResult,
    FactorInput,
    FactorLabelPolicy,
    FactorTransform,
)
from qts.research.factory.strategy_template import (
    StrategyTemplate,
    StrategyVariant,
    StrategyVariantFactory,
    StrategyVariantValidationResult,
)

__all__ = [
    "FactorDefinition",
    "FactorDefinitionDraft",
    "FactorDefinitionDraftConstraints",
    "FactorDefinitionValidationResult",
    "FactorDiscoveryDraftMapper",
    "FactorInput",
    "FactorLabelPolicy",
    "FactorTransform",
    "StrategyTemplate",
    "StrategyVariant",
    "StrategyVariantFactory",
    "StrategyVariantValidationResult",
]
