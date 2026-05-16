"""Verify repository architecture and domain-boundary guardrails."""

from __future__ import annotations

from qts.quality import guardrails as _guardrails

GuardrailViolation = _guardrails.GuardrailViolation
GuardrailSuite = _guardrails.GuardrailSuite
ImportBoundaryRule = _guardrails.ImportBoundaryRule
ProductSpecificRule = _guardrails.ProductSpecificRule
BrokerSpecificRule = _guardrails.BrokerSpecificRule
BrokerSymbolBoundaryRule = _guardrails.BrokerSymbolBoundaryRule
ProviderSdkImportRule = _guardrails.ProviderSdkImportRule
TestSupportRule = _guardrails.TestSupportRule
SharedCapabilityRule = _guardrails.SharedCapabilityRule
OOPPublicFactoryRule = _guardrails.OOPPublicFactoryRule
OOPHelperOwnershipRule = _guardrails.OOPHelperOwnershipRule
BacktestRunnerCohesionRule = _guardrails.BacktestRunnerCohesionRule
BacktestInputCohesionRule = _guardrails.BacktestInputCohesionRule
BacktestEngineCohesionRule = _guardrails.BacktestEngineCohesionRule
DataLiveNoSharedContractRule = _guardrails.DataLiveNoSharedContractRule
RemovedImportNoNewUsageRule = _guardrails.RemovedImportNoNewUsageRule
ProductionNoFakeClassRule = _guardrails.ProductionNoFakeClassRule
ProductionNoTestingImportRule = _guardrails.ProductionNoTestingImportRule
TransportCanonicalPathRule = _guardrails.TransportCanonicalPathRule
run_guardrails = _guardrails.run_guardrails
main = _guardrails.main


if __name__ == "__main__":
    raise SystemExit(main())
