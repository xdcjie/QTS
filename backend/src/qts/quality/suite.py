"""Guardrail suite registry and public execution entrypoint."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import QTS_ROOT, GuardrailViolation, RepositoryRule, Rule
from qts.quality.rules import (
    BacktestActorLoopCohesionRule,
    BacktestEngineCohesionRule,
    BacktestInputCohesionRule,
    BacktestRunnerCohesionRule,
    BrokerSpecificRule,
    BrokerSymbolBoundaryRule,
    CallerPresenceRule,
    ClassInventoryBudgetRule,
    DataLiveNoSharedContractRule,
    DuplicateDtoNameRule,
    EvidenceBundleRequiredForPromotionRule,
    IdeaRegistryRequiredForCandidateRule,
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
    PromotionConfigBoundaryRule,
    ProviderSdkImportRule,
    RemovedImportNoNewUsageRule,
    ResearchReportDecisionRequiredRule,
    ResearchRunScriptRule,
    ResearchStrategyStaleDocstringRule,
    ResearchWorkflowRuntimeKeyRule,
    RouteMetadataRequiredRule,
    RuntimeCoordinatorDecisionRule,
    RuntimeExecutionBoundaryRule,
    RuntimeSessionComplexityRule,
    SharedCapabilityRule,
    SharedRuntimeWordingRule,
    SingleFieldDtoJustificationRule,
    StaleArchitectureTextRule,
    StrategySdkPublicSurfaceRule,
    TestSupportRule,
    TradeDiagnosticsRequiredForPaperRule,
    TransportAdapterImportRule,
    TransportCanonicalPathRule,
    VwapOptimizerConfigRule,
)


class GuardrailSuite:
    """Execute a configured set of guardrail rules against Python files."""

    def __init__(
        self, rules: tuple[Rule, ...] | None = None, repo_root: Path | None = None
    ) -> None:
        self.rules = rules or (
            ImportBoundaryRule(),
            ProductSpecificRule(),
            BrokerSpecificRule(),
            BrokerSymbolBoundaryRule(),
            ProviderSdkImportRule(),
            RuntimeExecutionBoundaryRule(),
            TestSupportRule(),
            SharedCapabilityRule(),
            OOPPublicFactoryRule(),
            OOPHelperOwnershipRule(),
            BacktestRunnerCohesionRule(),
            BacktestInputCohesionRule(),
            BacktestEngineCohesionRule(),
            BacktestActorLoopCohesionRule(),
            StrategySdkPublicSurfaceRule(),
            LivePackageNoReplayClassRule(),
            DataLiveNoSharedContractRule(),
            TransportCanonicalPathRule(),
            TransportAdapterImportRule(),
            RemovedImportNoNewUsageRule(),
            ProductionNoFakeClassRule(),
            ProductionNoTestingImportRule(),
            SharedRuntimeWordingRule(),
            ProductionPlaceholderDocstringRule(),
            StaleArchitectureTextRule(),
            PlatformFreezeRule(repo_root=repo_root),
            RuntimeSessionComplexityRule(),
            RuntimeCoordinatorDecisionRule(),
            ClassInventoryBudgetRule(repo_root=repo_root),
            SingleFieldDtoJustificationRule(repo_root=repo_root),
            DuplicateDtoNameRule(),
            CallerPresenceRule(repo_root=repo_root),
            ResearchRunScriptRule(),
            VwapOptimizerConfigRule(),
            ProductionStrategyImportRule(),
            ResearchWorkflowRuntimeKeyRule(),
            EvidenceBundleRequiredForPromotionRule(),
            IdeaRegistryRequiredForCandidateRule(),
            PromotionConfigBoundaryRule(),
            TradeDiagnosticsRequiredForPaperRule(),
            RouteMetadataRequiredRule(),
            ResearchReportDecisionRequiredRule(),
            ResearchStrategyStaleDocstringRule(),
        )

    def check_file(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check_file."""
        violations: list[GuardrailViolation] = []
        for rule in self.rules:
            violations.extend(
                rule.check(
                    relative_path=relative_path,
                    qts_relative_path=qts_relative_path,
                    tree=tree,
                )
            )
        return violations

    def check(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform check."""
        source_root = repo_root / QTS_ROOT
        violations: list[GuardrailViolation] = []
        if source_root.exists():
            for path in sorted(source_root.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                relative_path = path.relative_to(repo_root)
                qts_relative_path = path.relative_to(repo_root / QTS_ROOT)
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(relative_path))
                violations.extend(
                    self.check_file(
                        relative_path=relative_path,
                        qts_relative_path=qts_relative_path,
                        tree=tree,
                    )
                )
        for rule in self.rules:
            if isinstance(rule, RepositoryRule):
                violations.extend(rule.check_repository(repo_root))
        return sorted(violations)


def run_guardrails(repo_root: Path) -> list[GuardrailViolation]:
    """Return all guardrail violations under the repository root."""
    return GuardrailSuite(repo_root=repo_root).check(repo_root)


def main() -> int:
    """Perform main."""
    repo_root = Path.cwd()
    violations = run_guardrails(repo_root)
    if not violations:
        print("Architecture guardrails passed.")
        return 0
    print("Architecture guardrails failed:")
    for violation in violations:
        print(f"  {violation.format()}")
    return 1


__all__ = ["GuardrailSuite", "main", "run_guardrails"]
