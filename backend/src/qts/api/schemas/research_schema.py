"""Research dashboard API response type aliases."""

from __future__ import annotations

from typing import TypeAlias

ResearchRunSchema: TypeAlias = dict[str, object]
ResearchRunListSchema: TypeAlias = tuple[ResearchRunSchema, ...]

ResearchReportSchema: TypeAlias = dict[str, object]
ResearchReportListSchema: TypeAlias = tuple[ResearchReportSchema, ...]

PromotionDecisionSchema: TypeAlias = dict[str, object]
PromotionDecisionListSchema: TypeAlias = tuple[PromotionDecisionSchema, ...]

StrategyLifecycleSchema: TypeAlias = dict[str, object]
StrategyLifecycleListSchema: TypeAlias = tuple[StrategyLifecycleSchema, ...]

ResearchRunComparisonSchema: TypeAlias = dict[str, object]

__all__ = [
    "PromotionDecisionListSchema",
    "PromotionDecisionSchema",
    "ResearchReportListSchema",
    "ResearchReportSchema",
    "ResearchRunComparisonSchema",
    "ResearchRunListSchema",
    "ResearchRunSchema",
    "StrategyLifecycleListSchema",
    "StrategyLifecycleSchema",
]
