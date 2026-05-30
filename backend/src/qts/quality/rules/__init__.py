"""Guardrail rule implementations grouped by rule family."""

from qts.quality.rules.account_mutation import AccountFillMutationRule
from qts.quality.rules.backtest_pipeline_cohesion import BacktestPipelineCohesionRule
from qts.quality.rules.boundaries import (
    BrokerSpecificRule,
    BrokerSymbolBoundaryRule,
    ProductSpecificRule,
    SharedCapabilityRule,
    StrategySdkPublicSurfaceRule,
    TestSupportRule,
)
from qts.quality.rules.caller_presence import CallerPresenceRule
from qts.quality.rules.config_loader_boundary import ConfigLoaderBoundaryRule
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
from qts.quality.rules.order_domain import OrderDomainTypingRule
from qts.quality.rules.public_boundary_exceptions import PublicBoundaryExceptionRule
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
from qts.quality.rules.runtime_private_access import RuntimePrivateAccessRule
from qts.quality.rules.snapshot import SnapshotCompletenessRule
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
    "BacktestPipelineCohesionRule",
    "BacktestRunnerCohesionRule",
    "BrokerSpecificRule",
    "BrokerSymbolBoundaryRule",
    "CallerPresenceRule",
    "ClassInventoryBudgetRule",
    "ConfigLoaderBoundaryRule",
    "DataLiveNoSharedContractRule",
    "DuplicateDtoNameRule",
    "EvidenceBundleRequiredForPromotionRule",
    "IdeaRegistryRequiredForCandidateRule",
    "ImportBoundaryRule",
    "LayerDependencyRule",
    "LivePackageNoReplayClassRule",
    "OOPHelperOwnershipRule",
    "OOPPublicFactoryRule",
    "OrderDomainTypingRule",
    "PlatformFreezeRule",
    "PromotionConfigBoundaryRule",
    "ProductSpecificRule",
    "ProductionStrategyImportRule",
    "ProductionNoFakeClassRule",
    "ProductionNoTestingImportRule",
    "ProductionPlaceholderDocstringRule",
    "PromotionValueHonestyRule",
    "ProviderSdkImportRule",
    "PublicBoundaryExceptionRule",
    "ResearchReportDecisionRequiredRule",
    "ResearchRunScriptRule",
    "ResearchStrategyStaleDocstringRule",
    "ResearchWorkflowRuntimeKeyRule",
    "RemovedImportNoNewUsageRule",
    "RouteMetadataRequiredRule",
    "RouteNoFakeDataRule",
    "RuntimeCoordinatorDecisionRule",
    "RuntimeExecutionBoundaryRule",
    "RuntimePrivateAccessRule",
    "RuntimeSessionComplexityRule",
    "SharedCapabilityRule",
    "SharedRuntimeWordingRule",
    "SingleFieldDtoJustificationRule",
    "SnapshotCompletenessRule",
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
