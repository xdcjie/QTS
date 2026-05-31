"""Verify repository architecture and domain-boundary guardrails."""

from __future__ import annotations

from pathlib import Path

from qts.quality import (
    BacktestActorLoopCohesionRule,
    BacktestEngineCohesionRule,
    BacktestInputCohesionRule,
    BacktestPipelineCohesionRule,
    BacktestRunnerCohesionRule,
    BrokerSpecificRule,
    BrokerSymbolBoundaryRule,
    CapabilityCompletenessRule,
    ClassInventoryBudgetRule,
    ConfigLoaderBoundaryRule,
    DataLiveNoSharedContractRule,
    DuplicateDtoNameRule,
    EvidenceBundleRequiredForPromotionRule,
    GuardrailRule,
    GuardrailViolation,
    IdeaRegistryRequiredForCandidateRule,
    ImportBoundaryRule,
    LivePackageNoReplayClassRule,
    OOPHelperOwnershipRule,
    OOPPublicFactoryRule,
    OperationsCommandRealityRule,
    OrderDomainTypingRule,
    PlatformFreezeRule,
    ProductionNoFakeClassRule,
    ProductionNoTestingImportRule,
    ProductionPlaceholderDocstringRule,
    ProductionStrategyImportRule,
    ProductSpecificRule,
    PromotionConfigBoundaryRule,
    PromotionValueHonestyRule,
    ProviderSdkImportRule,
    PublicBoundaryExceptionRule,
    PublicSurfaceRule,
    PyprojectQualityRule,
    RemovedImportNoNewUsageRule,
    ResearchReportDecisionRequiredRule,
    ResearchRunScriptRule,
    ResearchStrategyStaleDocstringRule,
    ResearchWorkflowRuntimeKeyRule,
    RouteMetadataRequiredRule,
    RouteNoFakeDataRule,
    RuntimeCoordinatorDecisionRule,
    RuntimeExecutionBoundaryRule,
    RuntimePrivateAccessRule,
    RuntimeSessionComplexityRule,
    SharedCapabilityRule,
    SharedRuntimeWordingRule,
    SingleFieldDtoJustificationRule,
    SnapshotCompletenessRule,
    StaleArchitectureTextRule,
    StrategySdkPublicSurfaceRule,
    TestSupportRule,
    TradeDiagnosticsRequiredForPaperRule,
    TransportAdapterImportRule,
    TransportCanonicalPathRule,
    VwapAdhocRunnerForbiddenRule,
    VwapOptimizerConfigRule,
)
from qts.quality import (
    GuardrailSuite as BaseGuardrailSuite,
)


class GuardrailSuite(BaseGuardrailSuite):
    """Script entrypoint suite backed by the canonical quality rule registry."""

    def __init__(
        self,
        rules: tuple[GuardrailRule, ...] | None = None,
        repo_root: Path | None = None,
    ) -> None:
        super().__init__(rules=rules, repo_root=repo_root)


def run_guardrails(repo_root: Path) -> list[GuardrailViolation]:
    """Return all guardrail violations under the repository root."""
    return GuardrailSuite(repo_root=repo_root).check(repo_root)


def main() -> int:
    """Run guardrails from the repository root."""
    repo_root = Path.cwd()
    violations = run_guardrails(repo_root)
    if not violations:
        print("Architecture guardrails passed.")
        return 0
    print("Architecture guardrails failed:")
    for violation in violations:
        print(f"  {violation.format()}")
    return 1


__all__ = [
    "BacktestActorLoopCohesionRule",
    "BacktestEngineCohesionRule",
    "BacktestInputCohesionRule",
    "BacktestPipelineCohesionRule",
    "BacktestRunnerCohesionRule",
    "BrokerSpecificRule",
    "BrokerSymbolBoundaryRule",
    "CapabilityCompletenessRule",
    "ClassInventoryBudgetRule",
    "ConfigLoaderBoundaryRule",
    "DataLiveNoSharedContractRule",
    "DuplicateDtoNameRule",
    "EvidenceBundleRequiredForPromotionRule",
    "GuardrailSuite",
    "GuardrailViolation",
    "IdeaRegistryRequiredForCandidateRule",
    "ImportBoundaryRule",
    "LivePackageNoReplayClassRule",
    "OOPHelperOwnershipRule",
    "OOPPublicFactoryRule",
    "OperationsCommandRealityRule",
    "OrderDomainTypingRule",
    "PlatformFreezeRule",
    "ProductSpecificRule",
    "ProductionNoFakeClassRule",
    "ProductionNoTestingImportRule",
    "ProductionPlaceholderDocstringRule",
    "ProductionStrategyImportRule",
    "PromotionConfigBoundaryRule",
    "PromotionValueHonestyRule",
    "ProviderSdkImportRule",
    "PublicBoundaryExceptionRule",
    "PublicSurfaceRule",
    "PyprojectQualityRule",
    "RemovedImportNoNewUsageRule",
    "ResearchReportDecisionRequiredRule",
    "ResearchRunScriptRule",
    "ResearchStrategyStaleDocstringRule",
    "ResearchWorkflowRuntimeKeyRule",
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
    "main",
    "run_guardrails",
]


if __name__ == "__main__":
    raise SystemExit(main())
