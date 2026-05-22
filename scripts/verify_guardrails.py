"""Verify repository architecture and domain-boundary guardrails."""

from __future__ import annotations

from pathlib import Path

from qts.quality import (
    BacktestActorLoopCohesionRule,
    BacktestEngineCohesionRule,
    BacktestInputCohesionRule,
    BacktestRunnerCohesionRule,
    BrokerSpecificRule,
    BrokerSymbolBoundaryRule,
    ClassInventoryBudgetRule,
    DataLiveNoSharedContractRule,
    DuplicateDtoNameRule,
    GuardrailRule,
    GuardrailViolation,
    ImportBoundaryRule,
    LivePackageNoReplayClassRule,
    OOPHelperOwnershipRule,
    OOPPublicFactoryRule,
    PlatformFreezeRule,
    ProductionNoFakeClassRule,
    ProductionNoTestingImportRule,
    ProductionPlaceholderDocstringRule,
    ProductionStrategyImportRule,
    ProductSpecificRule,
    ProviderSdkImportRule,
    RemovedImportNoNewUsageRule,
    ResearchRunScriptRule,
    ResearchWorkflowRuntimeKeyRule,
    RuntimeCoordinatorDecisionRule,
    RuntimeExecutionBoundaryRule,
    RuntimeSessionComplexityRule,
    SharedCapabilityRule,
    SharedRuntimeWordingRule,
    SingleFieldDtoJustificationRule,
    StaleArchitectureTextRule,
    StrategySdkPublicSurfaceRule,
    TestSupportRule,
    TransportAdapterImportRule,
    TransportCanonicalPathRule,
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
    "BacktestRunnerCohesionRule",
    "BrokerSpecificRule",
    "BrokerSymbolBoundaryRule",
    "ClassInventoryBudgetRule",
    "DataLiveNoSharedContractRule",
    "DuplicateDtoNameRule",
    "GuardrailSuite",
    "GuardrailViolation",
    "ImportBoundaryRule",
    "LivePackageNoReplayClassRule",
    "OOPHelperOwnershipRule",
    "OOPPublicFactoryRule",
    "PlatformFreezeRule",
    "ProductSpecificRule",
    "ProductionStrategyImportRule",
    "ProductionNoFakeClassRule",
    "ProductionNoTestingImportRule",
    "ProductionPlaceholderDocstringRule",
    "ProviderSdkImportRule",
    "ResearchRunScriptRule",
    "ResearchWorkflowRuntimeKeyRule",
    "RemovedImportNoNewUsageRule",
    "RuntimeCoordinatorDecisionRule",
    "RuntimeExecutionBoundaryRule",
    "RuntimeSessionComplexityRule",
    "SharedCapabilityRule",
    "SharedRuntimeWordingRule",
    "SingleFieldDtoJustificationRule",
    "StaleArchitectureTextRule",
    "StrategySdkPublicSurfaceRule",
    "TestSupportRule",
    "TransportAdapterImportRule",
    "TransportCanonicalPathRule",
    "VwapOptimizerConfigRule",
    "main",
    "run_guardrails",
]


if __name__ == "__main__":
    raise SystemExit(main())
