"""Boundaries guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import (
    BROKER_FACT_ALLOWED_PREFIXES,
    BROKER_SYMBOL_MAPPING_ALLOWED_PREFIXES,
    PRODUCT_FACT_ALLOWED_PREFIXES,
    GuardrailViolation,
    _check_broker_specific_code,
    _check_product_specific_code,
    _check_shared_capability_placement,
    _check_strategy_sdk_internal_leak,
    _check_test_support_code,
    _has_allowed_prefix,
    _iter_imported_names,
    _iter_imports,
)


class ProductSpecificRule:
    """Reject product hard-coding outside documented locations."""

    code = "PRODUCT_SPECIFIC_IMPLEMENTATION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag product hard-coding unless the path is an allowed product-fact prefix."""
        if _has_allowed_prefix(qts_relative_path, PRODUCT_FACT_ALLOWED_PREFIXES):
            return []
        return _check_product_specific_code(relative_path, qts_relative_path, tree)


class BrokerSpecificRule:
    """Reject broker hard-coding outside broker boundaries."""

    code = "BROKER_SPECIFIC_IMPLEMENTATION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag broker hard-coding unless the path is an allowed broker-fact prefix."""
        if _has_allowed_prefix(qts_relative_path, BROKER_FACT_ALLOWED_PREFIXES):
            return []
        return _check_broker_specific_code(relative_path, qts_relative_path, tree)


class BrokerSymbolBoundaryRule:
    """Reject broker symbol mapping imports outside approved boundary modules."""

    code = "BROKER_SYMBOL_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag BrokerSymbolMapping imports outside approved registry/adapter prefixes."""
        if _has_allowed_prefix(qts_relative_path, BROKER_SYMBOL_MAPPING_ALLOWED_PREFIXES):
            return []
        violations: list[GuardrailViolation] = []
        violation_lines: set[int] = set()
        for imported_module, line in _iter_imports(tree):
            if imported_module == "qts.registry.broker_symbol_mapping":
                violation_lines.add(line)
        for imported_module, imported_name, line in _iter_imported_names(tree):
            if imported_module == "qts.registry" and imported_name == "BrokerSymbolMapping":
                violation_lines.add(line)
        for line in sorted(violation_lines):
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message="BrokerSymbolMapping must stay at registry or adapter boundaries",
                )
            )
        return violations


class TestSupportRule:
    """Reject test/anchor support in production source."""

    code = "TEST_SUPPORT_IN_PRODUCTION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag test or anchor support code that appears in production source."""
        return _check_test_support_code(relative_path, qts_relative_path, tree)


class SharedCapabilityRule:
    """Reject shared capability semantics in source-specific modules."""

    code = "SHARED_CAPABILITY_IN_SOURCE_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag shared-capability semantics placed in source-specific modules."""
        return _check_shared_capability_placement(relative_path, qts_relative_path)


class StrategySdkPublicSurfaceRule:
    """Reject internal runtime/broker/risk/reconciliation symbols from public SDK modules."""

    code = "STRATEGY_SDK_INTERNAL_LEAK"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag internal runtime/broker/risk symbols leaking from public SDK modules."""
        return _check_strategy_sdk_internal_leak(relative_path, qts_relative_path, tree)


__all__ = [
    "BrokerSpecificRule",
    "BrokerSymbolBoundaryRule",
    "ProductSpecificRule",
    "SharedCapabilityRule",
    "StrategySdkPublicSurfaceRule",
    "TestSupportRule",
]
