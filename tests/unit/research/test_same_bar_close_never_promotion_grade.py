"""QTS-FINAL-004: ``same_bar_close`` results are never promotion-grade.

Optimistic same-bar look-ahead cannot back paper/live readiness evidence. The
explicit optimistic waiver authorizes research use of the policy but does not
make the resulting run promotion-grade.
"""

from __future__ import annotations

from qts.domain.execution_timing import ExecutionTimingModel, FillPolicy


def test_same_bar_close_with_waiver_is_not_promotion_grade() -> None:
    model = ExecutionTimingModel.research_only(optimistic_waiver=True)

    assert model.fill_policy is FillPolicy.SAME_BAR_CLOSE
    assert model.is_optimistic
    assert not model.is_promotion_grade
    assert model.to_manifest_payload()["promotion_grade"] is False


def test_next_bar_open_is_promotion_grade() -> None:
    model = ExecutionTimingModel.promotion_grade()

    assert model.fill_policy is FillPolicy.NEXT_BAR_OPEN
    assert model.is_promotion_grade


def test_only_next_bar_open_is_ever_promotion_grade() -> None:
    promotion_grade_policies = {policy for policy in FillPolicy if _is_promotion_grade(policy)}
    assert promotion_grade_policies == {FillPolicy.NEXT_BAR_OPEN}


def _is_promotion_grade(policy: FillPolicy) -> bool:
    waiver = policy is FillPolicy.SAME_BAR_CLOSE
    return ExecutionTimingModel(fill_policy=policy, optimistic_waiver=waiver).is_promotion_grade
