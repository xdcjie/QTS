"""Guardrail rule implementations grouped by rule family."""

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
from qts.quality.rules.runtime import (
    RuntimeCoordinatorDecisionRule,
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

__all__ = [
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
    "ImportBoundaryRule",
    "LivePackageNoReplayClassRule",
    "OOPHelperOwnershipRule",
    "OOPPublicFactoryRule",
    "PlatformFreezeRule",
    "ProductSpecificRule",
    "ProductionNoFakeClassRule",
    "ProductionNoTestingImportRule",
    "ProductionPlaceholderDocstringRule",
    "ProviderSdkImportRule",
    "RemovedImportNoNewUsageRule",
    "RuntimeCoordinatorDecisionRule",
    "RuntimeSessionComplexityRule",
    "SharedCapabilityRule",
    "SharedRuntimeWordingRule",
    "SingleFieldDtoJustificationRule",
    "StaleArchitectureTextRule",
    "StrategySdkPublicSurfaceRule",
    "TestSupportRule",
    "TransportAdapterImportRule",
    "TransportCanonicalPathRule",
]
