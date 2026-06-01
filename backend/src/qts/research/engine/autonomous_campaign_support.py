"""Stateful evidence/config support for the autonomous research engine.

Holds the campaign repo root and data-window cache, and owns the cross-cluster helper
methods (data/execution windows, config paths, policies/gauntlet/thresholds, idea and
budget payloads, future-chain install) extracted from AutonomousResearchEngine
(QTS-FINAL-011). The orchestration functions take a TrialEvidenceSupport-style support.
"""

from __future__ import annotations

import shutil
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from qts.data.historical.chains import HistoricalChain
from qts.research.audit_log import ResearchAuditLog
from qts.research.campaign import ResearchCampaignFamily
from qts.research.clock import ResearchClock, system_research_clock
from qts.research.engine.autonomous_engine_helpers import (
    _edge_type,
    _parse_timestamp,
    _template_idea_spec,
)
from qts.research.engine.autonomous_research_types import (
    AutonomousResearchRun,
)
from qts.research.factory.discovery_mapper import (
    FactorDefinitionDraftConstraints,
    FactorDiscoveryDraftMapper,
)
from qts.research.factory.factor_definition import FactorDefinition
from qts.research.idea_spec import IdeaSpec
from qts.research.metrics_schema import ResearchMetricsSchema
from qts.research.orchestrator import (
    ExperimentQueue,
    ExperimentRetryPolicy,
    ExperimentScheduler,
    ExperimentWorker,
    PromotionThresholds,
)
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentResult,
)
from qts.research.planner import (
    GenerationApprovalPolicy,
    GenerationApprovalRecord,
    NextGenerationProposal,
)
from qts.research.search import (
    SearchSpaceSpec,
    TrialBudgetLedger,
    TrialBudgetManager,
)
from qts.research.selector import (
    CorrelationGate,
    CostStressGate,
    DeflatedSharpeGate,
    FailureWindowVetoGate,
    PBOGate,
    SelectionPolicy,
    ValidationGauntlet,
)


class AutonomousResearchCampaignSupport:
    """Owns campaign evidence resolution, config/window builders, and policy payloads."""

    def __init__(self, *, repo_root: Path, clock: ResearchClock | None = None) -> None:
        """Bind the support to the campaign repo root; init the data-window cache."""
        self._repo_root = Path(repo_root)
        self._clock = clock or system_research_clock()
        self._data_window_cache: dict[tuple[str, int | None], tuple[str, str]] = {}

    def _run_experiment_job(
        self,
        job: ResearchExperimentJob,
        *,
        audit_log: ResearchAuditLog,
    ) -> ResearchExperimentResult:
        queue = ExperimentQueue(jobs=(job,))
        schedule = ExperimentScheduler(
            queue=queue,
            worker=ExperimentWorker(repo_root=self._repo_root, clock=self._clock),
            retry_policy=ExperimentRetryPolicy(max_attempts=1, clock=self._clock),
        ).run(audit_log=audit_log)
        if schedule.status != "completed":
            raise RuntimeError(f"experiment scheduler failed: {schedule.to_payload()}")
        if schedule.completed_job_ids != (job.job_id,):
            raise RuntimeError(f"unexpected completed experiment jobs: {schedule.to_payload()}")
        result_payload = (schedule.completed_results or {}).get(job.job_id)
        if result_payload is None:
            raise RuntimeError(f"completed experiment result missing: {job.job_id}")
        return ResearchExperimentResult.from_payload(result_payload)

    def _trial_budget_payload(
        self,
        *,
        run: AutonomousResearchRun,
        generation_id: str,
        trial: Mapping[str, Any],
        accepted: bool,
        decision_reason: str,
    ) -> dict[str, Any]:
        return {
            "accepted": accepted,
            "campaign_id": run.campaign_id,
            "compute_cost": 1,
            "decision_reason": decision_reason,
            "factor_family": str(trial["factor_family"]),
            "generation_id": generation_id,
            "idea_id": str(trial["idea_id"]),
            "strategy_family": str(trial["family"]),
            "time_window": f"{run.dataset_id}:{run.timeframe}",
            "trial_id": str(trial["trial_id"]),
        }

    def _candidate_generation_budget(
        self,
        run: AutonomousResearchRun,
        proposal: NextGenerationProposal | None,
    ) -> int:
        if proposal is None:
            return max(run.trials_per_generation, 1)
        return max(proposal.trial_budget, 0)

    def _idea_id(
        self,
        run: AutonomousResearchRun,
        family_id: str,
        proposal: NextGenerationProposal | None,
    ) -> str:
        if proposal is None:
            return f"idea-{run.campaign_id}-{family_id}"
        return f"idea-{run.campaign_id}-{family_id}-{proposal.next_generation_id}"

    def _search_space_from_path(
        self,
        path_text: str,
        universe: Sequence[str],
    ) -> SearchSpaceSpec:
        path = self._config_path(path_text)
        if not path.exists():
            raise FileNotFoundError(f"search-space config not found: {path}")
        return SearchSpaceSpec.from_yaml(path)

    def _factor_definition_for_family(
        self,
        *,
        run: AutonomousResearchRun,
        family: ResearchCampaignFamily,
        template_payload: Mapping[str, Any],
        static_factor_payload: Mapping[str, Any],
        path: Path,
    ) -> FactorDefinition:
        """Resolve the family factor definition, mapping a discovered idea when present.

        When the manifest template declares ``factor_discovery.idea_spec``, the
        discovered idea is mapped to a controlled FactorDefinition draft through
        ``FactorDiscoveryDraftMapper`` so a research idea actually drives the
        generated candidates. Ideas the deterministic mapper cannot place fall
        back to the static template definition, which always remains required.
        """
        idea_spec = _template_idea_spec(template_payload, path=path)
        if idea_spec is None:
            return FactorDefinition.from_payload(static_factor_payload)
        draft = FactorDiscoveryDraftMapper(
            constraints=FactorDefinitionDraftConstraints(roots=run.universe)
        ).draft_from_idea_spec(idea_spec)
        if draft.needs_human_spec or draft.factor_definition is None:
            return FactorDefinition.from_payload(static_factor_payload)
        return draft.factor_definition

    def _install_future_chain(
        self,
        *,
        root: str,
        source_data_path: Path,
        data_root: Path,
    ) -> tuple[Path, HistoricalChain]:
        source_chain_path = self._required_source_chain_path(
            root=root,
            source_data_path=source_data_path,
        )
        chains_dir = data_root / "chains"
        chains_dir.mkdir(parents=True, exist_ok=True)
        target_chain_path = chains_dir / f"{root}.json"
        shutil.copyfile(source_chain_path, target_chain_path)
        return target_chain_path, HistoricalChain.load(target_chain_path)

    def _required_source_chain_path(self, *, root: str, source_data_path: Path) -> Path:
        root = root.strip().upper()
        candidates = tuple(
            dict.fromkeys(
                (
                    source_data_path.parent.parent / "chains" / f"{root}.json",
                    self._repo_root / "historical" / "chains" / f"{root}.json",
                )
            )
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        searched = ", ".join(str(path) for path in candidates)
        raise FileNotFoundError(
            f"required future chain metadata is missing for {root}; searched: {searched}"
        )

    def _data_window(self, source_path: Path, *, max_rows: int | None) -> tuple[str, str]:
        cache_key = (str(source_path.resolve()), max_rows)
        cached = self._data_window_cache.get(cache_key)
        if cached is not None:
            return cached
        timestamps: list[str] = []
        seen_timestamps: set[str] = set()
        with source_path.open("r", encoding="utf-8") as source:
            header = source.readline().strip().split(",")
            if not header:
                raise ValueError(f"data path is empty: {source_path}")
            timestamp_index = header.index("ts_event" if "ts_event" in header else "timestamp")
            close_index = header.index("close")
            for line in source:
                if not line.strip():
                    continue
                values = line.strip().split(",")
                if "ts_event" in header and values[close_index].startswith("-"):
                    continue
                timestamp = values[timestamp_index]
                if timestamp in seen_timestamps:
                    continue
                seen_timestamps.add(timestamp)
                timestamps.append(timestamp)
                if max_rows is not None and len(timestamps) >= max_rows:
                    break
        if not timestamps:
            raise ValueError(f"data path has no timestamp rows: {source_path}")
        start = timestamps[0].replace(".000000000Z", "Z")
        end_timestamp = datetime.fromisoformat(
            timestamps[-1].replace(".000000000Z", "+00:00").replace("Z", "+00:00")
        )
        end = (end_timestamp + timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
        window = (start, end)
        self._data_window_cache[cache_key] = window
        return window

    def _backtest_window(self, run: AutonomousResearchRun, source_path: Path) -> tuple[str, str]:
        execution_window = self._execution_window(run)
        if execution_window is not None:
            return execution_window
        return self._data_window(source_path, max_rows=self._materialization_max_rows(run))

    def _execution_window(self, run: AutonomousResearchRun) -> tuple[str, str] | None:
        windows = self._execution_windows(run)
        if windows:
            return windows[0][0], windows[-1][1]
        execution = run.campaign_config.execution if run.campaign_config is not None else None
        if execution is not None and execution.start is not None and execution.end is not None:
            return execution.start, execution.end
        return None

    def _execution_windows(self, run: AutonomousResearchRun) -> tuple[tuple[str, str], ...]:
        execution = run.campaign_config.execution if run.campaign_config is not None else None
        if execution is None:
            return ()
        return tuple((str(window["start"]), str(window["end"])) for window in execution.windows)

    def _combined_data_window(
        self,
        paths: Sequence[Path],
        *,
        max_rows: int | None,
    ) -> dict[str, str]:
        windows = tuple(self._data_window(path, max_rows=max_rows) for path in paths)
        if not windows:
            raise ValueError("at least one data path is required")
        starts = tuple(_parse_timestamp(start) for start, _ in windows)
        ends = tuple(_parse_timestamp(end) for _, end in windows)
        return {
            "end": max(ends).isoformat(),
            "start": min(starts).isoformat(),
        }

    def _materialization_max_rows(self, run: AutonomousResearchRun) -> int | None:
        if run.campaign_config is None:
            raise ValueError("campaign execution.data_mode is required")
        execution = run.campaign_config.execution
        if execution.data_mode == "full":
            return None
        return execution.max_rows

    def _selection_policy(self, run: AutonomousResearchRun) -> SelectionPolicy:
        constraints = self._constraint_payload(run)
        return SelectionPolicy(
            max_drawdown=float(constraints.get("max_drawdown", 0.25)),
            min_oos_trade_count=int(constraints.get("min_oos_trade_count", 30)),
            min_profit_factor=float(constraints["min_profit_factor"])
            if "min_profit_factor" in constraints
            else None,
            max_selected=1,
            total_return_metric="performance.total_return",
            oos_sharpe_metric="performance.oos_sharpe",
            max_drawdown_metric="performance.max_drawdown",
            oos_trade_count_metric="trading.oos_trade_count",
            profit_factor_metric="quality.profit_factor",
            purpose="promotion",
            cost_sensitivity_metric="costs.cost_sensitivity",
        )

    def _promotion_thresholds(self, run: AutonomousResearchRun) -> PromotionThresholds:
        """Promotion-eligibility thresholds derived from the campaign constraints.

        ``min_oos_months`` is campaign policy: the derived oos_months *value*
        stays honestly computed from the validation windows, while the campaign
        declares the bar its data horizon can meet.
        """
        constraints = self._constraint_payload(run)
        return PromotionThresholds(min_oos_months=float(constraints.get("min_oos_months", 6.0)))

    def _metrics_schema(self) -> ResearchMetricsSchema:
        return ResearchMetricsSchema.from_yaml(
            self._repo_root / "configs" / "research" / "metrics" / "schema_v2.yaml"
        )

    def _validation_gauntlet(self, run: AutonomousResearchRun) -> ValidationGauntlet:
        constraints = self._constraint_payload(run)
        max_cost_impact = float(constraints.get("max_cost_impact", 0.25))
        return ValidationGauntlet(
            failure_window_gate=FailureWindowVetoGate(
                max_drawdown=float(constraints.get("max_drawdown", 0.25))
            ),
            cost_stress_gate=CostStressGate(
                max_degradation=max_cost_impact,
                max_slippage_sensitivity=max_cost_impact,
            ),
            correlation_gate=CorrelationGate(
                max_active_correlation=float(constraints.get("max_correlation_to_active", 0.80))
            ),
            # Multiple-testing / overfitting gates read the multiplicity-adjustment
            # evidence the selector records on each candidate (deflated Sharpe vs the
            # expected maximum over the trials tried, and PBO from the OOS return
            # series). They are no longer opt-out for autonomous promotion.
            deflated_sharpe_gate=DeflatedSharpeGate(),
            pbo_gate=PBOGate(),
            require_artifacts=True,
        )

    def _constraint_payload(self, run: AutonomousResearchRun) -> dict[str, float | int]:
        if run.campaign_config is None:
            return {
                "max_correlation_to_active": 0.50,
                "max_cost_impact": 0.25,
                "max_drawdown": 0.25,
                "min_oos_months": 12,
                "min_oos_trade_count": 40,
                "min_profit_factor": 1.15,
            }
        return {
            constraint.name: constraint.to_payload_value()
            for constraint in run.campaign_config.constraints
        }

    def _budget_manager(self, run: AutonomousResearchRun, root: Path) -> TrialBudgetManager:
        if run.campaign_config is None:
            return TrialBudgetManager(
                ledger=TrialBudgetLedger(root / "trial_budget_ledger.jsonl"),
                campaign_trial_limit=run.max_generations * run.trials_per_generation,
                strategy_family_trial_limit=run.max_generations * run.trials_per_generation,
                factor_family_trial_limit=run.max_generations * run.trials_per_generation,
            )
        budget = run.campaign_config.budget
        return TrialBudgetManager(
            ledger=TrialBudgetLedger(root / "trial_budget_ledger.jsonl"),
            campaign_trial_limit=budget.max_total_trials,
            strategy_family_trial_limit=budget.max_family_trials,
            factor_family_trial_limit=budget.max_family_trials,
            compute_budget_limit=budget.compute_budget_limit,
        )

    def _max_total_trials(self, run: AutonomousResearchRun) -> int:
        if run.campaign_config is not None:
            return run.campaign_config.budget.max_total_trials
        return run.max_generations * run.trials_per_generation

    def _generation_approval_payload(
        self,
        run: AutonomousResearchRun,
        proposal: NextGenerationProposal,
    ) -> dict[str, Any]:
        approval = self._approval_for(run, proposal)
        payload = GenerationApprovalPolicy().execution_payload(proposal, approval)
        return {
            **payload,
            "next_generation_id": proposal.next_generation_id,
        }

    def _approval_for(
        self,
        run: AutonomousResearchRun,
        proposal: NextGenerationProposal,
    ) -> GenerationApprovalRecord | None:
        for record in run.approval_records:
            if record.proposal_id == proposal.proposal_id:
                return record
        return None

    def _config_path(self, path_text: str) -> Path:
        path = Path(path_text)
        return path if path.is_absolute() else self._repo_root / path

    def _required_data_paths(
        self,
        run: AutonomousResearchRun,
    ) -> dict[str, Path]:
        if not run.data_paths:
            raise ValueError("autonomous research run requires explicit data_paths")
        paths = {str(root): Path(path) for root, path in run.data_paths.items()}
        missing_roots = [root for root in run.universe if root not in paths]
        if missing_roots:
            raise ValueError(f"data_paths missing roots: {', '.join(sorted(missing_roots))}")
        return paths

    def _idea(
        self,
        run: AutonomousResearchRun,
        generation_id: str,
        trial: Mapping[str, Any],
    ) -> IdeaSpec:
        family = str(trial["family"])
        return IdeaSpec(
            idea_id=f"idea-{run.campaign_id}-{generation_id}-{family}",
            title=f"{family} autonomous research candidate",
            hypothesis=f"{family} candidate remains research-only until human approval.",
            edge_type=_edge_type(family),
            source="autonomous_research_engine",
            created_at=self._clock.now(),
        )


__all__ = ["AutonomousResearchCampaignSupport"]
