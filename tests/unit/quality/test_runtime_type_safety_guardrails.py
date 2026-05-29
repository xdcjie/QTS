"""Guardrails for runtime type safety: typed enums, newtypes, and no list[Any] returns."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from qts.risk.config import RiskRuleName

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_SRC = REPO_ROOT / "backend" / "src"


class TestRiskRuleConfigUsesTypedName:
    """RiskRuleConfig.name must be RiskRuleName, not raw string."""

    def test_config_name_field_is_risk_rule_name_type(self) -> None:
        """The 'name' field annotation on RiskRuleConfig must be RiskRuleName."""
        source = Path("backend/src/qts/risk/config.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "RiskRuleConfig":
                for assign in node.body:
                    if isinstance(assign, ast.AnnAssign) and isinstance(assign.target, ast.Name):
                        if assign.target.id == "name":
                            # The annotation should reference RiskRuleName, not str.
                            assert isinstance(assign.annotation, ast.Name)
                            assert assign.annotation.id == "RiskRuleName"
                            return
        pytest.fail("RiskRuleConfig.name field not found")

    def test_risk_rule_name_enum_has_all_dispatch_values(self) -> None:
        """RiskRuleName must enumerate every dispatch string used by the registry."""
        expected_names = {
            "position_limit",
            "leverage_limit",
            "intraday_loss_limit",
            "concentration_limit",
            "max_notional",
            "max_order_quantity",
            "volatility_adjusted_sizing",
            "margin_limit",
            "market_data_permission",
            "market_data_freshness",
            "order_spec_validity",
        }
        actual_values = {member.value for member in RiskRuleName}
        assert actual_values == expected_names

    def test_risk_rule_registry_dispatches_by_enum_identity(self) -> None:
        """Registry dispatch must use `is RiskRuleName.X` comparisons, not raw strings."""
        source = (BACKEND_SRC / "qts" / "risk" / "rule_registry.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        # Find the build method body and check its if-statements only.
        build_body: list[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "RiskRuleRegistry":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "build":
                        build_body = item.body
                        break
        assert build_body, "RiskRuleRegistry.build method not found"
        for node in build_body:
            if isinstance(node, ast.If):
                # The test in each `if` should be config.name is RiskRuleName.X,
                # which is an ast.Compare with left=Attribute and comparator=Attribute.
                test = node.test
                if isinstance(test, ast.Compare):
                    for comparator in test.comparators:
                        if isinstance(comparator, ast.Constant) and isinstance(
                            comparator.value, str
                        ):
                            pytest.fail(
                                f"Found raw string comparison in build dispatch: "
                                f"'{comparator.value}' -- use RiskRuleName enum instead"
                            )


class TestNoPublicListAnyReturnInRuntime:
    """Runtime modules must not expose public functions returning list[Any]."""

    @pytest.mark.parametrize(
        "module_path",
        [
            "qts/runtime/actors/account_actor.py",
            "qts/runtime/actors/order_manager_actor.py",
            "qts/runtime/intent_processing.py",
            "qts/risk/risk_engine.py",
            "qts/risk/rule_registry.py",
        ],
    )
    def test_no_list_any_return(self, module_path: str) -> None:
        """Public functions in runtime modules must not have list[Any] return annotations."""
        filepath = BACKEND_SRC / module_path
        if not filepath.exists():
            pytest.skip(f"{module_path} not found")
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Only check public functions (not starting with _).
                if node.name.startswith("_"):
                    continue
                if node.returns is None:
                    continue
                # Check for list[Any] pattern in return annotation.
                ann = node.returns
                if isinstance(ann, ast.Subscript):
                    if isinstance(ann.value, ast.Name) and ann.value.id == "list":
                        if isinstance(ann.slice, ast.Name) and ann.slice.id == "Any":
                            pytest.fail(
                                f"Public function '{node.name}' in {module_path} "
                                f"returns list[Any] -- use a typed list[T] instead"
                            )
