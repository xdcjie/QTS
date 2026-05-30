"""Gate tests for the value-honesty guardrails (C5).

``RouteNoFakeDataRule`` and ``PromotionValueHonestyRule`` defend the
"shipped value must be real, not faked" invariant. Each test pairs a positive
case (the real, service-backed / artifact-derived code passes) with a negative
case (a synthetic hardcoded-value violation is caught).
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation
from qts.quality.rules.value_honesty import (
    PromotionValueHonestyRule,
    RouteNoFakeDataRule,
)

_QTS_ROOT = Path("backend/src/qts")


def _check_route(source: str, qts_rel: str) -> list[GuardrailViolation]:
    return RouteNoFakeDataRule().check(
        relative_path=_QTS_ROOT / qts_rel,
        qts_relative_path=Path(qts_rel),
        tree=ast.parse(source),
    )


def _check_promotion(source: str, qts_rel: str) -> list[GuardrailViolation]:
    return PromotionValueHonestyRule().check(
        relative_path=_QTS_ROOT / qts_rel,
        qts_relative_path=Path(qts_rel),
        tree=ast.parse(source),
    )


# --- RouteNoFakeDataRule ------------------------------------------------------

_FAKE_ROUTE = """
from fastapi import APIRouter
from qts.api.schemas.common import OrderStatusSchema

router = APIRouter(prefix="/orders")


@router.get("/{order_id}", response_model=OrderStatusSchema)
def order_status(order_id: str) -> OrderStatusSchema:
    return OrderStatusSchema(order_id="X", status="filled", filled_quantity=5)
"""

_SERVICE_BACKED_ROUTE = """
from fastapi import APIRouter
from qts.api.mappers import map_order_status_dto
from qts.api.schemas.common import OrderStatusSchema
from qts.application.services import OrderQueryService

router = APIRouter(prefix="/orders")
_orders = OrderQueryService()


@router.get("/{order_id}", response_model=OrderStatusSchema)
def order_status(order_id: str) -> OrderStatusSchema:
    return map_order_status_dto(_orders.order_status(order_id))
"""


def test_business_route_returning_hardcoded_schema_is_flagged() -> None:
    violations = _check_route(_FAKE_ROUTE, "api/routes/orders.py")
    assert [v.code for v in violations] == ["ROUTE_NO_FAKE_DATA"]
    assert violations[0].symbol == "order_status"


def test_service_backed_route_is_not_flagged() -> None:
    assert _check_route(_SERVICE_BACKED_ROUTE, "api/routes/orders.py") == []


def test_health_probe_route_returning_literal_is_out_of_scope() -> None:
    source = """
from fastapi import APIRouter

router = APIRouter()


@router.get("/health/liveness")
def liveness() -> dict[str, str]:
    return {"status": "live"}
"""
    assert _check_route(source, "api/routes/health.py") == []


def test_real_business_routes_pass() -> None:
    routes_dir = _QTS_ROOT / "api" / "routes"
    for module in ("strategies", "orders", "accounts", "operations"):
        path = routes_dir / f"{module}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        violations = RouteNoFakeDataRule().check(
            relative_path=path,
            qts_relative_path=Path("api/routes") / f"{module}.py",
            tree=tree,
        )
        assert violations == [], f"{module} routes flagged: {violations}"


# --- PromotionValueHonestyRule -----------------------------------------------

_FAKE_PROMOTION = """
def build_derivation(reader):
    deterministic_replay_passed = True
    return Derivation(
        no_lookahead_passed=True,
        promotion_eligible=True,
    )


def build_payload():
    return {"cost_stress_accepted": True}
"""

_DERIVED_PROMOTION = """
def build_derivation(reader):
    deterministic_replay_passed = bool(reader.read("deterministic_replay"))
    no_lookahead_passed = _derive_no_lookahead(reader)
    return Derivation(
        deterministic_replay_passed=deterministic_replay_passed,
        no_lookahead_passed=no_lookahead_passed,
        promotion_eligible=_derive_eligible(deterministic_replay_passed, no_lookahead_passed),
    )
"""


def test_hardcoded_true_verdict_fields_are_flagged() -> None:
    violations = _check_promotion(_FAKE_PROMOTION, "research/orchestrator/x.py")
    flagged = sorted({v.symbol for v in violations})
    assert flagged == [
        "cost_stress_accepted",
        "deterministic_replay_passed",
        "no_lookahead_passed",
        "promotion_eligible",
    ]
    assert all(v.code == "PROMOTION_VALUE_HONESTY" for v in violations)


def test_derived_verdict_fields_are_not_flagged() -> None:
    assert _check_promotion(_DERIVED_PROMOTION, "research/orchestrator/x.py") == []


def test_dry_run_false_default_is_not_flagged() -> None:
    # The real dry-run metrics default assigns ``promotion_eligible`` to False,
    # which must never trip the literal-True gate.
    source = 'def m():\n    return {"promotion_eligible": False}\n'
    assert _check_promotion(source, "research/metrics.py") == []


def test_non_research_module_is_out_of_scope() -> None:
    source = "def m():\n    promotion_eligible = True\n    return promotion_eligible\n"
    assert _check_promotion(source, "api/routes/orders.py") == []


def test_real_research_modules_pass() -> None:
    research_dir = _QTS_ROOT / "research"
    for path in sorted(research_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        violations = PromotionValueHonestyRule().check(
            relative_path=path,
            qts_relative_path=path.relative_to(_QTS_ROOT),
            tree=tree,
        )
        assert violations == [], f"{path} flagged: {violations}"
