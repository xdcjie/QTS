"""Guardrail rule implementations grouped by rule family."""

from qts.quality.rules.account_mutation import AccountFillMutationRule
from qts.quality.rules.boundaries import (
    BrokerSpecificRule,
    BrokerSymbolBoundaryRule,
    ProductSpecificRule,
    SharedCapabilityRule,
    StrategySdkPublicSurfaceRule,
    TestSupportRule,
)
from qts.quality.rules.caller_presence import CallerPresenceRule
from qts.quality.rules.docstrings import ProductionPlaceholderDocstringRule
from qts.quality.rules.flows import (
    ProductionStrategyImportRule,
    ResearchRunScriptRule,
    ResearchWorkflowRuntimeKeyRule,
    VwapAdhocRunnerForbiddenRule,
    VwapOptimizerConfigRule,
    VwapTaxonomyPresenceRule,
)
from qts.quality.rules.imports import (
    ImportBoundaryRule,
    ProductionNoTestingImportRule,
    ProviderSdkImportRule,
    RemovedImportNoNewUsageRule,
)
from qts.quality.rules.inventory import (
    ClassInventoryBudgetRule,
    DuplicateDtoNameRule,
    PlatformFreezeRule,
    SingleFieldDtoJustificationRule,
)
from qts.quality.rules.layering import LayerDependencyRule
from qts.quality.rules.live import (
    DataLiveNoSharedContractRule,
    LivePackageNoReplayClassRule,
    SharedRuntimeWordingRule,
)
from qts.quality.rules.oop import (
    BacktestActorLoopCohesionRule,
    BacktestEngineCohesionRule,
    BacktestInputCohesionRule,
    BacktestRunnerCohesionRule,
    OOPHelperOwnershipRule,
    OOPPublicFactoryRule,
)
from qts.quality.rules.research import (
    EvidenceBundleRequiredForPromotionRule,
    IdeaRegistryRequiredForCandidateRule,
    PromotionConfigBoundaryRule,
    ResearchReportDecisionRequiredRule,
    ResearchStrategyStaleDocstringRule,
    RouteMetadataRequiredRule,
    TradeDiagnosticsRequiredForPaperRule,
)
from qts.quality.rules.runtime import (
    RuntimeCoordinatorDecisionRule,
    RuntimeExecutionBoundaryRule,
    RuntimeSessionComplexityRule,
)
from qts.quality.rules.stale import (
    ProductionNoFakeClassRule,
    StaleArchitectureTextRule,
)
from qts.quality.rules.transport import (
    TransportAdapterImportRule,
    TransportCanonicalPathRule,
)
from qts.quality.rules.value_honesty import (
    PromotionValueHonestyRule,
    RouteNoFakeDataRule,
)

__all__ = [
    "AccountFillMutationRule",
    "BacktestActorLoopCohesionRule",
    "BacktestEngineCohesionRule",
    "BacktestInputCohesionRule",
    "BacktestRunnerCohesionRule",
    "BrokerSpecificRule",
    "BrokerSymbolBoundaryRule",
    "CallerPresenceRule",
    "ClassInventoryBudgetRule",
    "DataLiveNoSharedContractRule",
    "DuplicateDtoNameRule",
    "EvidenceBundleRequiredForPromotionRule",
    "IdeaRegistryRequiredForCandidateRule",
    "ImportBoundaryRule",
    "LayerDependencyRule",
    "LivePackageNoReplayClassRule",
    "OOPHelperOwnershipRule",
    "OOPPublicFactoryRule",
    "PlatformFreezeRule",
    "PromotionConfigBoundaryRule",
    "ProductSpecificRule",
    "ProductionStrategyImportRule",
    "ProductionNoFakeClassRule",
    "ProductionNoTestingImportRule",
    "ProductionPlaceholderDocstringRule",
    "PromotionValueHonestyRule",
    "ProviderSdkImportRule",
    "ResearchReportDecisionRequiredRule",
    "ResearchRunScriptRule",
    "ResearchStrategyStaleDocstringRule",
    "ResearchWorkflowRuntimeKeyRule",
    "RemovedImportNoNewUsageRule",
    "RouteMetadataRequiredRule",
    "RouteNoFakeDataRule",
    "RuntimeCoordinatorDecisionRule",
    "RuntimeExecutionBoundaryRule",
    "RuntimeSessionComplexityRule",
    "SharedCapabilityRule",
    "SharedRuntimeWordingRule",
    "SingleFieldDtoJustificationRule",
    "StaleArchitectureTextRule",
    "StrategySdkPublicSurfaceRule",
    "TestSupportRule",
    "TradeDiagnosticsRequiredForPaperRule",
    "TransportAdapterImportRule",
    "TransportCanonicalPathRule",
    "VwapAdhocRunnerForbiddenRule",
    "VwapOptimizerConfigRule",
    "VwapTaxonomyPresenceRule",
]
