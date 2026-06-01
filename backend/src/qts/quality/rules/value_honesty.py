"""Value-honesty guardrail rules.

Two static checks that defend the "shipped value must be real, not faked"
invariant (CLAUDE.md §6 backtest/live parity and §11 production wiring):

- ``RouteNoFakeDataRule`` rejects a business API route handler that returns a
  business DTO/schema built entirely from literal constants without consulting
  any injected service. Such a handler ships a hardcoded answer that bypasses
  the application/service boundary.
- ``PromotionValueHonestyRule`` rejects assigning a promotion-verdict field
  (``*_passed``, ``*_accepted``, ``accepted``, ``consistent``, ``passed``,
  ``promotion_eligible``) to the literal ``True`` in production research
  metric/evidence code. Verdicts must be derived from artifacts/inputs, never
  asserted as a constant.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

# Business route modules under api/routes/. Health/version/schema and other
# infra routes legitimately return literals (probe payloads) and are out of
# scope; only domain routes that must be service-backed are checked.
_BUSINESS_ROUTE_MODULES = frozenset({"strategies", "orders", "accounts", "operations"})
_ROUTE_DECORATOR_ATTRS = frozenset({"get", "post", "put", "patch", "delete"})
# A constructed value is treated as a "business value" when it builds a schema /
# DTO object or a mapping. Returning such an object built only from constants,
# with no service consulted, is the fake-data anti-pattern this rule catches.
_BUSINESS_VALUE_SUFFIXES = ("Schema", "DTO")

# Promotion-verdict fields must be derived, never set to a literal ``True``.
_VERDICT_FIELD_SUFFIXES = ("_passed", "_accepted")
_VERDICT_FIELD_NAMES = frozenset({"accepted", "consistent", "passed", "promotion_eligible"})


class RouteNoFakeDataRule:
    """Reject business route handlers that return literal-only business data."""

    code = "ROUTE_NO_FAKE_DATA"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag literal-only business route handlers."""
        if qts_relative_path.parts[:2] != ("api", "routes"):
            return []
        if qts_relative_path.stem not in _BUSINESS_ROUTE_MODULES:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if not self._is_route_handler(node):
                continue
            if not self._returns_business_value(node):
                continue
            if self._consults_service(node):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=node.lineno,
                    message=(
                        f"business route handler {node.name!r} returns a hardcoded business "
                        "value without consulting an injected service; route the response "
                        "through an application/query service instead of literal constants"
                    ),
                    remediation=(
                        "Back the route with an application/query service and map its "
                        "result, rather than returning constant schema/DTO literals."
                    ),
                    symbol=node.name,
                )
            )
        return violations

    @staticmethod
    def _is_route_handler(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Return whether the function is decorated with ``@router.<method>(...)``."""
        for decorator in node.decorator_list:
            call = decorator if isinstance(decorator, ast.Call) else None
            target = call.func if call is not None else decorator
            if isinstance(target, ast.Attribute) and target.attr in _ROUTE_DECORATOR_ATTRS:
                return True
        return False

    @classmethod
    def _returns_business_value(cls, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Return whether any ``return`` produces a constructed business value."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and cls._is_business_value(child.value):
                return True
        return False

    @classmethod
    def _is_business_value(cls, value: ast.expr | None) -> bool:
        if value is None:
            return False
        if isinstance(value, ast.Dict):
            return True
        if isinstance(value, ast.Call):
            name = cls._called_name(value.func)
            return name is not None and name.endswith(_BUSINESS_VALUE_SUFFIXES)
        if isinstance(value, ast.List | ast.Tuple | ast.Set):
            return any(cls._is_business_value(element) for element in value.elts)
        return False

    @classmethod
    def _consults_service(cls, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Return whether the handler calls into an injected service or mapper.

        A real handler either invokes a method on a collaborator (``Attribute``
        call such as ``_orders.order_status(...)``) or delegates to a mapper /
        service helper function (``map_*`` / ``*_dto`` / ``*_service``). Pure
        schema/DTO construction calls and validation helpers do not count. Only
        the body is scanned -- the ``@router.<method>(...)`` decorator is itself
        an attribute call and must not satisfy the gate.
        """
        for statement in node.body:
            for child in ast.walk(statement):
                if not isinstance(child, ast.Call):
                    continue
                func = child.func
                if isinstance(func, ast.Attribute):
                    return True
                name = cls._called_name(func)
                if name is None:
                    continue
                if name.startswith("map_") or name.endswith(("_dto", "_service", "Service")):
                    return True
        return False

    @staticmethod
    def _called_name(func: ast.expr) -> str | None:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None


class PromotionValueHonestyRule:
    """Reject hardcoding promotion-verdict fields to the literal ``True``."""

    code = "PROMOTION_VALUE_HONESTY"

    # Research modules whose job is deriving promotion verdicts / metrics. Other
    # research files may set the same field names from real inputs; the value
    # honesty contract is that none of them assigns the literal ``True``.
    _SCOPE_PREFIX = ("research",)

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag verdict fields assigned to a literal ``True`` in research code."""
        if qts_relative_path.parts[: len(self._SCOPE_PREFIX)] != self._SCOPE_PREFIX:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            for field_name, line in self._literal_true_verdicts(node):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=(
                            f"promotion-verdict field {field_name!r} is hardcoded to True; "
                            "derive it from validation artifacts/inputs"
                        ),
                        remediation=(
                            "Derive promotion verdicts from validation artifacts or upstream "
                            "metrics; never assign a constant True to an accepted / consistent / "
                            "passed / *_passed / *_accepted / promotion_eligible field."
                        ),
                        symbol=field_name,
                    )
                )
        return violations

    @classmethod
    def _literal_true_verdicts(cls, node: ast.AST) -> list[tuple[str, int]]:
        """Return ``(field_name, line)`` for verdict fields assigned literal True."""
        results: list[tuple[str, int]] = []
        if isinstance(node, ast.keyword):
            if node.arg is not None and cls._is_verdict_field(node.arg) and _is_true(node.value):
                results.append((node.arg, _node_line(node.value)))
        elif isinstance(node, ast.Assign):
            if _is_true(node.value):
                for target in node.targets:
                    name = cls._assign_target_name(target)
                    if name is not None and cls._is_verdict_field(name):
                        results.append((name, node.lineno))
        elif isinstance(node, ast.AnnAssign):
            name = cls._assign_target_name(node.target)
            if name is not None and cls._is_verdict_field(name) and _is_true(node.value):
                results.append((name, node.lineno))
        elif isinstance(node, ast.Dict):
            for key, dict_value in zip(node.keys, node.values, strict=True):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and cls._is_verdict_field(key.value)
                    and _is_true(dict_value)
                ):
                    results.append((key.value, _node_line(dict_value)))
        return results

    @staticmethod
    def _assign_target_name(target: ast.expr) -> str | None:
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            return target.attr
        return None

    @staticmethod
    def _is_verdict_field(name: str) -> bool:
        return name in _VERDICT_FIELD_NAMES or name.endswith(_VERDICT_FIELD_SUFFIXES)


def _is_true(value: ast.expr | None) -> bool:
    return isinstance(value, ast.Constant) and value.value is True


def _node_line(node: ast.AST) -> int:
    try:
        return int(object.__getattribute__(node, "lineno"))
    except AttributeError:
        return 1


__all__ = ["PromotionValueHonestyRule", "RouteNoFakeDataRule"]
