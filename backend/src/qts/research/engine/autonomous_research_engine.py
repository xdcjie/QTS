"""Bounded autonomous research loop for research-only campaign artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.artifact_graph import (
    ResearchArtifactEdge,
    ResearchArtifactGraph,
    ResearchArtifactGraphWriter,
    ResearchArtifactNode,
)
from qts.research.audit_log import ResearchAuditLog
from qts.research.campaign import ResearchCampaignConfig, ResearchCampaignFamily
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.factory.factor_definition import FactorDefinition
from qts.research.factory.strategy_template import StrategyTemplate, StrategyVariantFactory
from qts.research.idea_spec import IdeaSpec
from qts.research.landscape import FitnessAnalytics, FitnessLandscapePoint, FitnessLandscapeStore
from qts.research.metrics_schema import ResearchMetricsSchema
from qts.research.orchestrator import (
    ExperimentQueue,
    ExperimentRetryPolicy,
    ExperimentScheduler,
    ExperimentWorker,
)
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentResult,
    ResearchExperimentRunner,
    ResearchTrialResult,
)
from qts.research.planner import (
    GenerationApprovalPolicy,
    GenerationApprovalRecord,
    NextGenerationProposal,
)
from qts.research.promotion_packet import PromotionPacketV2
from qts.research.search import (
    CandidateGenerator,
    SearchSpaceSpec,
    TrialBudgetLedger,
    TrialBudgetManager,
)
from qts.research.selector import (
    CandidateSelector,
    CorrelationGate,
    CostStressGate,
    FailureWindowVetoGate,
    SelectionPolicy,
    ValidationGauntlet,
)


@dataclass(frozen=True, slots=True)
class AutonomousResearchRun:
    """Configuration for one bounded autonomous research campaign."""

    campaign_id: str
    output_root: Path
    universe: tuple[str, ...]
    families: tuple[str, ...]
    max_generations: int
    trials_per_generation: int
    data_paths: Mapping[str, Path] | None = None
    calendar: str = "research-calendar"
    timeframe: str = "1m"
    dataset_id: str = "research-data-contract"
    approval_policy: str = "manual_gate"
    campaign_config: ResearchCampaignConfig | None = None
    approval_records: tuple[GenerationApprovalRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.campaign_id.strip():
            raise ValueError("campaign_id is required")
        if not self.universe:
            raise ValueError("universe must not be empty")
        if not self.families:
            raise ValueError("families must not be empty")
        if self.max_generations < 1:
            raise ValueError("max_generations must be positive")
        if self.trials_per_generation < 1:
            raise ValueError("trials_per_generation must be positive")
        object.__setattr__(self, "output_root", Path(self.output_root))
        object.__setattr__(self, "universe", tuple(str(item) for item in self.universe))
        object.__setattr__(self, "families", tuple(str(item) for item in self.families))
        object.__setattr__(
            self,
            "data_paths",
            None
            if self.data_paths is None
            else {str(root): Path(path) for root, path in self.data_paths.items()},
        )
        object.__setattr__(self, "approval_records", tuple(self.approval_records))

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        data_paths: Mapping[str, str | Path] | None = None,
        output_root: str | Path | None = None,
        approval_records: Sequence[GenerationApprovalRecord] = (),
    ) -> AutonomousResearchRun:
        """Load a campaign run from a validated ResearchCampaignConfig YAML file."""

        config_path = Path(path)
        campaign = ResearchCampaignConfig.from_yaml(config_path)
        return cls(
            campaign_id=campaign.campaign_id,
            output_root=Path(output_root)
            if output_root is not None
            else Path("runs/research/acceptance") / campaign.campaign_id,
            universe=campaign.universe.roots,
            families=tuple(family.id for family in campaign.families),
            max_generations=campaign.budget.max_generations,
            trials_per_generation=campaign.budget.max_trials_per_generation,
            data_paths=None
            if data_paths is None
            else {str(root): Path(path) for root, path in data_paths.items()},
            calendar=campaign.universe.calendar,
            timeframe=campaign.universe.timeframe,
            dataset_id=campaign.universe.dataset_id,
            campaign_config=campaign,
            approval_records=tuple(approval_records),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready campaign payload."""

        return {
            "approval_policy": self.approval_policy,
            "budget": {
                "max_generations": self.max_generations,
                "trials_per_generation": self.trials_per_generation,
            },
            "campaign_id": self.campaign_id,
            "campaign_config": None
            if self.campaign_config is None
            else self.campaign_config.to_payload(),
            "calendar": self.calendar,
            "data_paths": {
                root: str(path) for root, path in sorted((self.data_paths or {}).items())
            },
            "dataset_id": self.dataset_id,
            "families": list(self.families),
            "generation_approval_hashes": [
                record.approval_hash for record in self.approval_records
            ],
            "output_root": str(self.output_root),
            "timeframe": self.timeframe,
            "universe": list(self.universe),
        }


@dataclass(frozen=True, slots=True)
class AutonomousResearchGeneration:
    """Artifacts produced by one autonomous generation."""

    generation_id: str
    trial_count: int
    selected_count: int
    rejected_count: int
    audit_record_count: int
    landscape_path: Path
    next_generation_proposal_path: Path
    experiment_result: ResearchExperimentResult

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready generation summary."""

        return {
            "audit_record_count": self.audit_record_count,
            "experiment_result": self.experiment_result.to_payload(),
            "generation_id": self.generation_id,
            "landscape_path": str(self.landscape_path),
            "next_generation_proposal_path": str(self.next_generation_proposal_path),
            "rejected_count": self.rejected_count,
            "selected_count": self.selected_count,
            "trial_count": self.trial_count,
        }


@dataclass(frozen=True, slots=True)
class AutonomousResearchResult:
    """Final autonomous campaign artifact index."""

    status: str
    output_root: Path
    generations: tuple[AutonomousResearchGeneration, ...]
    fitness_landscape_path: Path
    fitness_analytics_path: Path
    next_generation_proposal_path: Path
    selected_candidates_path: Path
    rejected_candidates_path: Path
    validation_summary_path: Path
    report_path: Path
    audit_log_path: Path
    artifact_graph_path: Path
    paper_live_launches: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready result payload."""

        return {
            "artifact_graph_path": str(self.artifact_graph_path),
            "audit_log_path": str(self.audit_log_path),
            "fitness_analytics_path": str(self.fitness_analytics_path),
            "fitness_landscape_path": str(self.fitness_landscape_path),
            "generations": [generation.to_payload() for generation in self.generations],
            "next_generation_proposal_path": str(self.next_generation_proposal_path),
            "output_root": str(self.output_root),
            "paper_live_launches": list(self.paper_live_launches),
            "rejected_candidates_path": str(self.rejected_candidates_path),
            "report_path": str(self.report_path),
            "selected_candidates_path": str(self.selected_candidates_path),
            "status": self.status,
            "validation_summary_path": str(self.validation_summary_path),
        }


class AutonomousResearchEngine:
    """Run bounded research-only generations and produce promotion evidence."""

    def __init__(self, *, repo_root: Path) -> None:
        self._repo_root = Path(repo_root)
        self._data_window_cache: dict[tuple[str, int | None], tuple[str, str]] = {}

    def run(self, run: AutonomousResearchRun) -> AutonomousResearchResult:
        """Run a bounded autonomous campaign without launching runtime modes."""

        root = run.output_root
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)
        self._write_json(root / "campaign_config.json", run.to_payload())
        data_paths = self._required_data_paths(run)
        audit_log = ResearchAuditLog(root / "audit" / "audit_log.jsonl")
        evidence_registry = EvidenceRegistry(root / "evidence")
        landscape_store = FitnessLandscapeStore(root / "fitness_landscape.jsonl")
        budget_manager = self._budget_manager(run, root)

        all_trial_evidence_rows: list[dict[str, Any]] = []
        selected_rows: list[dict[str, Any]] = []
        rejected_rows: list[dict[str, Any]] = []
        generations: list[AutonomousResearchGeneration] = []
        next_proposal: NextGenerationProposal | None = None
        stop_status: str | None = None
        approval_reasons: tuple[str, ...] = ()

        for generation_index in range(run.max_generations):
            active_proposal: NextGenerationProposal | None = None
            if generation_index > 0:
                if next_proposal is None:
                    raise RuntimeError("next-generation proposal missing")
                approval_payload = self._generation_approval_payload(run, next_proposal)
                audit_log.append(
                    "generation_approval_decided",
                    approval_payload,
                    created_at=datetime(2026, 5, 26, tzinfo=UTC)
                    + timedelta(seconds=generation_index),
                )
                if approval_payload["accepted"] is not True:
                    stop_status = "pending_human_approval"
                    approval_reasons = tuple(str(reason) for reason in approval_payload["reasons"])
                    break
                active_proposal = next_proposal
            generation = self._run_generation(
                run=run,
                generation_index=generation_index,
                proposal=active_proposal,
                data_paths=data_paths,
                audit_log=audit_log,
                evidence_registry=evidence_registry,
                landscape_store=landscape_store,
                budget_manager=budget_manager,
            )
            generations.append(generation["generation"])
            all_trial_evidence_rows.extend(generation["trial_evidence_rows"])
            selected_rows.extend(generation["selected_rows"])
            rejected_rows.extend(generation["rejected_rows"])
            next_proposal = cast(NextGenerationProposal, generation["next_generation_proposal"])

        fitness_landscape_path = root / "fitness_landscape.jsonl"
        selected_candidates_path = root / "selected_candidates.jsonl"
        rejected_candidates_path = root / "rejected_candidates.jsonl"
        self._write_jsonl(selected_candidates_path, selected_rows)
        self._write_jsonl(rejected_candidates_path, rejected_rows)

        fitness_analytics_path = root / "fitness_analytics.json"
        analytics = FitnessAnalytics.from_landscape(landscape_store.read())
        self._write_json(fitness_analytics_path, analytics.to_payload())
        next_generation_proposal_path = root / "next_generation_proposal.json"
        if next_proposal is None:
            self._write_json(next_generation_proposal_path, {})
        else:
            self._write_next_generation_proposal(next_generation_proposal_path, next_proposal)
        self._write_jsonl(
            root / "candidate_parameters.jsonl",
            self._candidate_parameter_rows_from_trial_evidence(all_trial_evidence_rows),
        )

        report_path = root / "report.md"
        self._write_report(
            report_path,
            campaign_id=run.campaign_id,
            selected_count=len(selected_rows),
            rejected_count=len(rejected_rows),
        )
        validation_summary_path = root / "validation_summary.json"
        validation_summary = {
            "approval_reasons": list(approval_reasons),
            "campaign_id": run.campaign_id,
            "generation_count": len(generations),
            "generated_candidate_count": len(selected_rows) + len(rejected_rows),
            "landscape_trial_count": len(landscape_store.read().points),
            "promotion_packet_count": len(selected_rows),
            "rejected_candidate_count": len(rejected_rows),
            "status": stop_status or ("accepted" if selected_rows else "rejected"),
        }
        self._write_json(validation_summary_path, validation_summary)
        artifact_graph_path = (
            self._write_final_artifact_graph(
                root=root,
                selected_rows=selected_rows,
                report_path=report_path,
                audit_log=audit_log,
            )
            if selected_rows
            else self._write_empty_artifact_graph(root)
        )

        return AutonomousResearchResult(
            status=str(validation_summary["status"]),
            output_root=root,
            generations=tuple(generations),
            fitness_landscape_path=fitness_landscape_path,
            fitness_analytics_path=fitness_analytics_path,
            next_generation_proposal_path=next_generation_proposal_path,
            selected_candidates_path=selected_candidates_path,
            rejected_candidates_path=rejected_candidates_path,
            validation_summary_path=validation_summary_path,
            report_path=report_path,
            audit_log_path=audit_log.path,
            artifact_graph_path=artifact_graph_path,
            paper_live_launches=(),
        )

    def _run_generation(
        self,
        *,
        run: AutonomousResearchRun,
        generation_index: int,
        proposal: NextGenerationProposal | None,
        data_paths: Mapping[str, Path],
        audit_log: ResearchAuditLog,
        evidence_registry: EvidenceRegistry,
        landscape_store: FitnessLandscapeStore,
        budget_manager: TrialBudgetManager,
    ) -> dict[str, Any]:
        generation_id = f"generation-{generation_index:03d}"
        generation_dir = run.output_root / generation_id
        generation_dir.mkdir(parents=True, exist_ok=True)
        budget_rejected_rows: list[dict[str, Any]] = []
        trials = self._trials(
            run,
            generation_id,
            generation_index,
            proposal=proposal,
            budget_manager=budget_manager,
            audit_log=audit_log,
            budget_rejected_rows=budget_rejected_rows,
        )
        self._write_jsonl(
            generation_dir / "candidate_parameters.jsonl",
            self._candidate_parameter_rows_from_trials(trials),
        )
        checked_paths = tuple(str(path) for path in data_paths.values())
        job = ResearchExperimentJob(
            job_id=f"{run.campaign_id}-{generation_id}",
            generation_id=generation_id,
            manifest_payload=self._manifest_payload(run, checked_paths, data_paths),
            output_root=run.output_root,
            trials=trials,
        )
        experiment_result = self._run_experiment_job(job, audit_log=audit_log)
        trial_evidence_rows = self._trial_evidence_rows(
            run=run,
            generation_id=generation_id,
            trials=trials,
            trial_results=experiment_result.trials,
        )
        self._append_trial_audit_records(
            audit_log=audit_log,
            generation_index=generation_index,
            trial_evidence_rows=trial_evidence_rows,
        )
        selected_rows, execution_rejected_rows = self._select_generation_candidates(
            run=run,
            generation_id=generation_id,
            trials=trials,
            trial_results=experiment_result.trials,
            trial_evidence_rows=trial_evidence_rows,
            evidence_registry=evidence_registry,
            audit_log=audit_log,
        )
        rejected_rows = [*execution_rejected_rows, *budget_rejected_rows]
        generation_landscape_rows = self._append_landscape_points(
            run=run,
            landscape_store=landscape_store,
            rows=(*selected_rows, *execution_rejected_rows, *budget_rejected_rows),
        )
        landscape_path = generation_dir / "fitness_landscape.jsonl"
        proposal_path = generation_dir / "next_generation_proposal.json"
        self._write_jsonl(landscape_path, generation_landscape_rows)
        next_proposal = self._next_generation_proposal(
            run=run,
            previous_generation_id=generation_id,
            analytics=FitnessAnalytics.from_landscape(landscape_store.read()),
            accepted_trial_count=len(landscape_store.read().points),
            data_window=self._combined_data_window(
                tuple(data_paths.values()),
                max_rows=self._materialization_max_rows(run),
            ),
        )
        self._write_next_generation_proposal(proposal_path, next_proposal)
        audit_log.append(
            "next_generation_proposed",
            next_proposal.to_payload(),
            created_at=datetime(2026, 5, 26, tzinfo=UTC)
            + timedelta(seconds=500 + generation_index),
        )
        return {
            "generation": AutonomousResearchGeneration(
                generation_id=generation_id,
                trial_count=len(trials) + len(budget_rejected_rows),
                selected_count=len(selected_rows),
                rejected_count=len(rejected_rows),
                audit_record_count=len(audit_log.list()),
                landscape_path=landscape_path,
                next_generation_proposal_path=proposal_path,
                experiment_result=experiment_result,
            ),
            "trial_evidence_rows": trial_evidence_rows,
            "next_generation_proposal": next_proposal,
            "rejected_rows": rejected_rows,
            "selected_rows": selected_rows,
        }

    def _run_experiment_job(
        self,
        job: ResearchExperimentJob,
        *,
        audit_log: ResearchAuditLog,
    ) -> ResearchExperimentResult:
        queue = ExperimentQueue(jobs=(job,))
        schedule = ExperimentScheduler(
            queue=queue,
            worker=ExperimentWorker(repo_root=self._repo_root),
            retry_policy=ExperimentRetryPolicy(max_attempts=1),
        ).run(audit_log=audit_log)
        if schedule.status != "completed":
            raise RuntimeError(f"experiment scheduler failed: {schedule.to_payload()}")
        if schedule.completed_job_ids != (job.job_id,):
            raise RuntimeError(f"unexpected completed experiment jobs: {schedule.to_payload()}")
        result_payload = (schedule.completed_results or {}).get(job.job_id)
        if result_payload is None:
            raise RuntimeError(f"completed experiment result missing: {job.job_id}")
        return ResearchExperimentResult.from_payload(result_payload)

    def _trials(
        self,
        run: AutonomousResearchRun,
        generation_id: str,
        generation_index: int,
        *,
        proposal: NextGenerationProposal | None,
        budget_manager: TrialBudgetManager,
        audit_log: ResearchAuditLog,
        budget_rejected_rows: list[dict[str, Any]],
    ) -> tuple[Mapping[str, Any], ...]:
        trials: list[Mapping[str, Any]] = []
        for generated_trial in self._generated_trials(
            run,
            generation_id,
            generation_index,
            proposal=proposal,
        ):
            trial_id = str(generated_trial["trial_id"])
            decision = budget_manager.request_trial(
                trial_id=trial_id,
                campaign_id=run.campaign_id,
                generation_id=generation_id,
                strategy_family=str(generated_trial["family"]),
                factor_family=str(generated_trial["factor_family"]),
                idea_id=str(generated_trial["idea_id"]),
                time_window=f"{run.dataset_id}:{run.timeframe}",
                compute_cost=1,
                created_at=datetime(2026, 5, 26, tzinfo=UTC)
                + timedelta(seconds=(generation_index * 1000) + len(trials)),
            )
            record = budget_manager.ledger.list()[-1]
            audit_log.append(
                "trial_budget_decision",
                record.payload,
                created_at=record.created_at,
            )
            if not decision.accepted:
                budget_rejected_rows.append(
                    self._budget_rejected_row(
                        run=run,
                        generation_id=generation_id,
                        trial=generated_trial,
                        budget_record_id=record.record_id,
                        decision_reason=decision.reason,
                    )
                )
                continue
            trials.append(generated_trial)
            if len(trials) >= run.trials_per_generation:
                break
        return tuple(trials)

    def _generated_trials(
        self,
        run: AutonomousResearchRun,
        generation_id: str,
        generation_index: int,
        *,
        proposal: NextGenerationProposal | None,
    ) -> tuple[Mapping[str, Any], ...]:
        candidate_budget = self._candidate_generation_budget(run, proposal)
        family_candidates: list[tuple[Mapping[str, Any], tuple[Any, ...]]] = []
        for family in self._ordered_family_specs(self._family_specs(run), proposal):
            generator = CandidateGenerator(family["search_space"])
            candidates = generator.grid(
                budget=self._family_candidate_budget(
                    family_id=str(family["family_id"]),
                    base_budget=candidate_budget + generation_index,
                    proposal=proposal,
                )
            )
            if generation_index:
                candidates = candidates[generation_index:] or candidates
            family_candidates.append((family, candidates))
        generated: list[Mapping[str, Any]] = []
        for family, candidate in self._round_robin_candidates(family_candidates):
            parameters = dict(candidate.parameters)
            template = self._proposal_adjusted_template(
                cast(StrategyTemplate, family["template"]),
                proposal,
            )
            variant = StrategyVariantFactory(template).create_variant(
                parameters,
                allowed_roots=run.universe,
            )
            ordinal = len(generated)
            trial_id = f"{generation_id}-trial-{ordinal:03d}"
            root = str(parameters.get("root", run.universe[0]))
            generated.append(
                {
                    "backtest_pipeline": self._backtest_pipeline_payload(
                        run=run,
                        trial_id=trial_id,
                        root=root,
                        parameters=parameters,
                        strategy_entrypoint=variant.strategy_entrypoint,
                    ),
                    "candidate_id": candidate.candidate_id,
                    "candidate_space_hash": candidate.candidate_space_hash,
                    "factor_family": variant.family,
                    "factor_hash": variant.factor_hash,
                    "family": family["family_id"],
                    "idea_id": self._idea_id(run, str(family["family_id"]), proposal),
                    "manifest_patch": self._proposal_manifest_patch(
                        variant.to_manifest_patch(),
                        proposal,
                    ),
                    "parameters": parameters,
                    "proposal_application": self._proposal_application_payload(proposal),
                    "strategy_variant_hash": variant.variant_hash,
                    "strategy_variant_id": variant.variant_id,
                    "trial_id": trial_id,
                    "validation": {"artifacts_required": True},
                }
            )
        return tuple(generated)

    def _candidate_generation_budget(
        self,
        run: AutonomousResearchRun,
        proposal: NextGenerationProposal | None,
    ) -> int:
        if proposal is None:
            return max(run.trials_per_generation, 1)
        return max(proposal.trial_budget, 0)

    def _ordered_family_specs(
        self,
        family_specs: Sequence[Mapping[str, Any]],
        proposal: NextGenerationProposal | None,
    ) -> tuple[Mapping[str, Any], ...]:
        focus_order = self._focused_family_order(proposal)
        return tuple(
            sorted(
                family_specs,
                key=lambda family: (
                    focus_order.index(str(family["family_id"]))
                    if str(family["family_id"]) in focus_order
                    else len(focus_order),
                    str(family["family_id"]),
                ),
            )
        )

    def _family_candidate_budget(
        self,
        *,
        family_id: str,
        base_budget: int,
        proposal: NextGenerationProposal | None,
    ) -> int:
        budget = max(base_budget, 0)
        if proposal is None:
            return budget
        for mutation in proposal.mutations:
            if (
                getattr(mutation, "mutation_type", "") == "family_budget"
                and mutation.action == "reduce_family_budget"
                and mutation.target == family_id
            ):
                budget = min(budget, max(1, budget // 2))
        return budget

    def _round_robin_candidates(
        self,
        family_candidates: Sequence[tuple[Mapping[str, Any], tuple[Any, ...]]],
    ) -> tuple[tuple[Mapping[str, Any], Any], ...]:
        rows: list[tuple[Mapping[str, Any], Any]] = []
        max_length = max((len(candidates) for _, candidates in family_candidates), default=0)
        for index in range(max_length):
            for family, candidates in family_candidates:
                if index < len(candidates):
                    rows.append((family, candidates[index]))
        return tuple(rows)

    def _focused_family_order(self, proposal: NextGenerationProposal | None) -> tuple[str, ...]:
        if proposal is None:
            return ()
        focused: list[str] = []
        for mutation in proposal.mutations:
            if (
                getattr(mutation, "mutation_type", "") != "search_space"
                or mutation.action != "focus_best_family"
            ):
                continue
            payload_family = mutation.payload.get("strategy_family")
            family_id = str(payload_family or mutation.target.split(".", maxsplit=1)[0])
            if family_id and family_id not in focused:
                focused.append(family_id)
        return tuple(focused)

    def _proposal_adjusted_template(
        self,
        template: StrategyTemplate,
        proposal: NextGenerationProposal | None,
    ) -> StrategyTemplate:
        if proposal is None:
            return template
        risk_assumptions = dict(template.risk_assumptions)
        execution_assumptions = dict(template.execution_assumptions)
        changed = False
        for mutation in proposal.mutations:
            if getattr(mutation, "mutation_type", "") != "strategy_variant":
                continue
            if mutation.action == "add_stop_or_vol_target":
                risk_assumptions["proposal_risk_control"] = mutation.mutation_id
                risk_assumptions["volatility_target_required"] = True
                changed = True
            elif mutation.action == "increase_min_hold_bars":
                execution_assumptions["proposal_execution_control"] = mutation.mutation_id
                execution_assumptions["min_hold_bars"] = max(
                    2,
                    int(execution_assumptions.get("min_hold_bars", 1)),
                )
                changed = True
        if not changed:
            return template
        return replace(
            template,
            risk_assumptions=risk_assumptions,
            execution_assumptions=execution_assumptions,
        )

    def _proposal_manifest_patch(
        self,
        manifest_patch: Mapping[str, Any],
        proposal: NextGenerationProposal | None,
    ) -> dict[str, Any]:
        patch = dict(manifest_patch)
        application = self._proposal_application_payload(proposal)
        if not application:
            return patch
        research_factory = self._mapping(patch.get("research_factory", {}), "research_factory")
        patch["research_factory"] = {
            **research_factory,
            "proposal_application": application,
        }
        return patch

    def _idea_id(
        self,
        run: AutonomousResearchRun,
        family_id: str,
        proposal: NextGenerationProposal | None,
    ) -> str:
        if proposal is None:
            return f"idea-{run.campaign_id}-{family_id}"
        return f"idea-{run.campaign_id}-{family_id}-{proposal.next_generation_id}"

    def _proposal_application_payload(
        self,
        proposal: NextGenerationProposal | None,
    ) -> dict[str, Any]:
        if proposal is None:
            return {}
        return {
            "applied": True,
            "mutation_ids": [mutation.mutation_id for mutation in proposal.mutations],
            "proposal_hash": proposal.proposal_hash,
            "proposal_id": proposal.proposal_id,
            "source_generation_id": proposal.previous_generation_id,
        }

    def _budget_rejected_row(
        self,
        *,
        run: AutonomousResearchRun,
        generation_id: str,
        trial: Mapping[str, Any],
        budget_record_id: str,
        decision_reason: str,
    ) -> dict[str, Any]:
        return {
            "budget_record_id": budget_record_id,
            "budget_rejected": True,
            "campaign_id": run.campaign_id,
            "candidate_id": str(trial["candidate_id"]),
            "candidate_space_hash": str(trial["candidate_space_hash"]),
            "family": str(trial["family"]),
            "factor_family": str(trial["factor_family"]),
            "generation_id": generation_id,
            "parameters": dict(self._mapping(trial["parameters"], "parameters")),
            "proposal_application": dict(
                self._mapping(trial.get("proposal_application", {}), "proposal_application")
            ),
            "reasons": [decision_reason],
            "rejection_stage": "trial_budget",
            "selector_reasons": [],
            "gauntlet_reasons": [],
            "stage": "trial_budget",
            "status": "rejected",
            "strategy_variant_hash": str(trial["strategy_variant_hash"]),
            "strategy_variant_id": str(trial["strategy_variant_id"]),
            "trial_id": str(trial["trial_id"]),
        }

    def _family_specs(self, run: AutonomousResearchRun) -> tuple[Mapping[str, Any], ...]:
        if run.campaign_config is None:
            raise ValueError("autonomous research engine requires ResearchCampaignConfig")
        specs: list[Mapping[str, Any]] = []
        for family in run.campaign_config.families:
            search_space = self._search_space_from_path(family.search_space, run.universe)
            specs.append(
                {
                    "family_id": family.id,
                    "search_space": search_space,
                    "template": self._strategy_template(run, family, search_space),
                }
            )
        return tuple(specs)

    def _search_space_from_path(
        self,
        path_text: str,
        universe: Sequence[str],
    ) -> SearchSpaceSpec:
        path = self._config_path(path_text)
        if not path.exists():
            raise FileNotFoundError(f"search-space config not found: {path}")
        return SearchSpaceSpec.from_yaml(path)

    def _strategy_template(
        self,
        run: AutonomousResearchRun,
        family: ResearchCampaignFamily,
        search_space: SearchSpaceSpec,
    ) -> StrategyTemplate:
        path = self._config_path(family.manifest_template)
        if not path.exists():
            raise FileNotFoundError(f"strategy template config not found: {path}")
        payload = self._yaml_mapping(path)
        factor_payload = payload.get("factor_definition")
        if not isinstance(factor_payload, Mapping):
            raise ValueError(f"strategy template factor_definition is required: {path}")
        factor_definition = FactorDefinition.from_payload(cast(Mapping[str, Any], factor_payload))
        return StrategyTemplate(
            template_id=str(payload.get("template_id", f"{family.template}_template")),
            family=family.id,
            factor_definition=factor_definition,
            strategy_entrypoint=str(
                payload.get("strategy_entrypoint", f"strategies.research.{family.id}:Strategy")
            ),
            allowed_imports=tuple(str(item) for item in payload.get("allowed_imports", ())),
            parameter_space=self._parameter_space_payload(search_space),
            risk_assumptions=self._mapping(
                payload.get("risk_assumptions", {"max_position_notional": 100000}),
                "risk_assumptions",
            ),
            execution_assumptions=self._mapping(
                payload.get("execution_assumptions", {"slippage_bps": 1}),
                "execution_assumptions",
            ),
            manifest_template=self._mapping(payload.get("manifest_template", {}), "manifest"),
        )

    def _parameter_space_payload(self, search_space: SearchSpaceSpec) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        conditional_parameters = {
            constraint.parameter
            for constraint in search_space.constraints
            if constraint.constraint_type == "conditional" and constraint.parameter is not None
        }
        for parameter in search_space.parameters:
            values = parameter.finite_values()
            if values is not None:
                field_payload: dict[str, Any] = {"values": list(values)}
                if parameter.name in conditional_parameters:
                    field_payload["optional"] = True
                payload[parameter.name] = field_payload
        return payload

    def _backtest_pipeline_payload(
        self,
        *,
        run: AutonomousResearchRun,
        trial_id: str,
        root: str,
        parameters: Mapping[str, Any],
        strategy_entrypoint: str,
    ) -> dict[str, Any]:
        backtest_config_path, data_quality_path = self._write_backtest_config(
            run=run,
            trial_id=trial_id,
            root=root,
            strategy_entrypoint=strategy_entrypoint,
        )
        strategy_parameter_map: dict[str, str] = {}
        strategy_parameter_defaults: dict[str, Any] = {"symbols": [root]}
        if "lookback" in parameters:
            strategy_parameter_map["lookback"] = "long_window"
            strategy_parameter_defaults["short_window"] = 1
        if "long_window" in parameters:
            strategy_parameter_map["long_window"] = "long_window"
        if "short_window" in parameters:
            strategy_parameter_map["short_window"] = "short_window"
        if not strategy_parameter_map:
            strategy_parameter_defaults["long_window"] = 2
            strategy_parameter_map["threshold"] = "long_window"
        return {
            "backtest_config_path": str(backtest_config_path),
            "data_quality_paths": [str(data_quality_path)],
            "objective_metric": "sharpe_ratio",
            "strategy_parameter_defaults": strategy_parameter_defaults,
            "strategy_parameter_map": strategy_parameter_map,
        }

    def _write_backtest_config(
        self,
        *,
        run: AutonomousResearchRun,
        trial_id: str,
        root: str,
        strategy_entrypoint: str,
    ) -> tuple[Path, Path]:
        data_paths = self._required_data_paths(run)
        data_config_path, data_quality_path = self._write_backtest_data_config(
            run=run,
            trial_id=trial_id,
            root=root,
            data_path=data_paths[root],
        )
        start, end = self._data_window(
            data_paths[root],
            max_rows=self._materialization_max_rows(run),
        )
        config_path = run.output_root / "backtest_configs" / f"{trial_id}.yaml"
        payload = {
            "end": end,
            "initial_cash": "1000000",
            "instrument_ids": {root: f"DATASET.{root}"},
            "market_data": {
                "catalog": "research",
                "config": str(data_config_path),
                "source": "local_historical",
            },
            "risk_config": {"max_notional": "100000000"},
            "roots": [root],
            "start": start,
            "strategy_class": strategy_entrypoint,
            "strategy_params": {"long_window": 2, "short_window": 1, "symbols": [root]},
            "symbols": [root],
            "timeframe": run.timeframe,
            "warmup_bars": 0,
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return config_path, data_quality_path

    def _write_backtest_data_config(
        self,
        *,
        run: AutonomousResearchRun,
        trial_id: str,
        root: str,
        data_path: Path,
    ) -> tuple[Path, Path]:
        max_rows = self._materialization_max_rows(run)
        data_root = (
            run.output_root / "backtest_data" / "full" / root
            if max_rows is None
            else run.output_root / "backtest_data" / trial_id
        )
        bars_dir = data_root / "data"
        bars_dir.mkdir(parents=True, exist_ok=True)
        target_csv = bars_dir / f"{root}.csv"
        if max_rows is None:
            self._ensure_full_backtest_csv(data_path, target_csv, symbol=root)
        else:
            self._materialize_backtest_csv(data_path, target_csv, symbol=root, max_rows=max_rows)
        config_path = data_root / "historical.local.yaml"
        payload = {
            "historical_data": {
                "catalogs": {
                    "research": {
                        "datasets": {
                            root: {
                                "asset_class": "future",
                                "bars": [{"file": target_csv.name, "timeframe": run.timeframe}],
                                "exchange": run.calendar,
                            }
                        },
                        "store": "local_csv",
                    }
                },
                "stores": {
                    "local_csv": {
                        "bars_dir": "data",
                        "root_dir": str(data_root),
                        "type": "local_csv",
                    }
                },
            }
        }
        config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return config_path, target_csv

    def _ensure_full_backtest_csv(
        self, source_path: Path, target_path: Path, *, symbol: str
    ) -> None:
        metadata_path = target_path.with_suffix(".materialization.json")
        source_stat = source_path.stat()
        expected_metadata = {
            "max_rows": None,
            "source_path": str(source_path),
            "source_size": source_stat.st_size,
            "source_mtime_ns": source_stat.st_mtime_ns,
            "symbol": symbol,
        }
        if target_path.exists() and metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata == expected_metadata:
                return
        temp_path = target_path.with_suffix(f"{target_path.suffix}.tmp")
        self._materialize_backtest_csv(source_path, temp_path, symbol=symbol, max_rows=None)
        temp_path.replace(target_path)
        self._write_json(metadata_path, expected_metadata)

    def _materialize_backtest_csv(
        self,
        source_path: Path,
        target_path: Path,
        *,
        symbol: str,
        max_rows: int | None,
    ) -> None:
        with (
            source_path.open("r", encoding="utf-8") as source,
            target_path.open(
                "w",
                encoding="utf-8",
            ) as target,
        ):
            header_line = source.readline()
            if not header_line:
                raise ValueError(f"data path is empty: {source_path}")
            header = header_line.strip().split(",")
            target.write(
                "ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n"
            )
            emitted = 0
            seen_timestamps: set[str] = set()
            if "ts_event" in header:
                timestamp_index = header.index("ts_event")
                open_index = header.index("open")
                high_index = header.index("high")
                low_index = header.index("low")
                close_index = header.index("close")
                volume_index = header.index("volume")
                for source_index, line in enumerate(source, start=1):
                    if max_rows is not None and emitted >= max_rows:
                        break
                    if not line.strip():
                        continue
                    values = line.strip().split(",")
                    timestamp = values[timestamp_index]
                    if timestamp in seen_timestamps:
                        continue
                    close = values[close_index]
                    if close.startswith("-"):
                        continue
                    seen_timestamps.add(timestamp)
                    target.write(
                        ",".join(
                            (
                                timestamp,
                                "33",
                                "1",
                                str(source_index),
                                values[open_index],
                                values[high_index],
                                values[low_index],
                                close,
                                values[volume_index],
                                symbol,
                            )
                        )
                        + "\n"
                    )
                    emitted += 1
                if emitted:
                    return
                raise ValueError(f"data path has no positive OHLCV rows: {source_path}")
            if header != ["timestamp", "close"]:
                raise ValueError(
                    f"unsupported research CSV columns for backtest pipeline: {source_path}"
                )
            for index, line in enumerate(source, start=1):
                if max_rows is not None and emitted >= max_rows:
                    break
                if not line.strip():
                    continue
                timestamp, close = line.strip().split(",", maxsplit=1)
                target.write(
                    f"{timestamp},33,1,{index},{close},{close},{close},{close},1,{symbol}\n"
                )
                emitted += 1

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

    def _combined_data_window(
        self,
        paths: Sequence[Path],
        *,
        max_rows: int | None,
    ) -> dict[str, str]:
        windows = tuple(self._data_window(path, max_rows=max_rows) for path in paths)
        if not windows:
            raise ValueError("at least one data path is required")
        starts = tuple(self._parse_timestamp(start) for start, _ in windows)
        ends = tuple(self._parse_timestamp(end) for _, end in windows)
        return {
            "end": max(ends).isoformat(),
            "start": min(starts).isoformat(),
        }

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value.replace(".000000000Z", "+00:00").replace("Z", "+00:00"))

    def _materialization_max_rows(self, run: AutonomousResearchRun) -> int | None:
        if run.campaign_config is None:
            raise ValueError("campaign execution.data_mode is required")
        execution = run.campaign_config.execution
        if execution.data_mode == "full":
            return None
        return execution.max_rows

    def _manifest_payload(
        self,
        run: AutonomousResearchRun,
        checked_paths: tuple[str, ...],
        data_paths: Mapping[str, Path],
    ) -> dict[str, Any]:
        data_window = self._combined_data_window(
            tuple(data_paths.values()),
            max_rows=self._materialization_max_rows(run),
        )
        return {
            "campaign_id": run.campaign_id,
            "data": {
                "calendar": run.calendar,
                "checked_paths": list(checked_paths),
                "dataset_id": run.dataset_id,
                "end": data_window["end"],
                "materialization": {
                    "data_mode": (
                        None
                        if run.campaign_config is None
                        else run.campaign_config.execution.data_mode
                    ),
                    "max_rows": (
                        None
                        if run.campaign_config is None
                        else run.campaign_config.execution.max_rows
                    ),
                },
                "start": data_window["start"],
                "timeframe": run.timeframe,
            },
            "run": {
                "created_at": "2026-05-26T00:00:00+00:00",
                "id": run.campaign_id,
                "owner": "research",
                "question": "bounded autonomous research campaign",
            },
            "strategy": {
                "id": f"{run.campaign_id}_strategy",
                "source_module": f"strategies.research.{run.campaign_id}",
                "target_module": f"strategies.production.{run.campaign_id}",
            },
        }

    def _trial_evidence_rows(
        self,
        *,
        run: AutonomousResearchRun,
        generation_id: str,
        trials: Sequence[Mapping[str, Any]],
        trial_results: Sequence[ResearchTrialResult],
    ) -> list[dict[str, Any]]:
        by_trial_id = {result.trial_id: result for result in trial_results}
        rows: list[dict[str, Any]] = []
        for trial in trials:
            trial_id = str(trial["trial_id"])
            result = by_trial_id[trial_id]
            metrics = self._metrics_from_trial_result(result)
            quality = self._mapping(metrics["quality"], "quality")
            trading = self._mapping(metrics["trading"], "trading")
            rows.append(
                {
                    "campaign_id": run.campaign_id,
                    "candidate_id": str(trial["candidate_id"]),
                    "candidate_space_hash": str(trial["candidate_space_hash"]),
                    "evidence_bundle_id": result.evidence_bundle_id,
                    "family": str(trial["family"]),
                    "factor_family": str(trial["factor_family"]),
                    "factor_hash": str(trial["factor_hash"]),
                    "generation_id": generation_id,
                    "manifest_hash": result.manifest_hash,
                    "metrics": dict(metrics),
                    "metrics_path": str(result.metrics_path),
                    "objective_value": quality["sharpe"],
                    "parameters": dict(self._mapping(trial["parameters"], "parameters")),
                    "proposal_application": dict(
                        self._mapping(
                            trial.get("proposal_application", {}),
                            "proposal_application",
                        )
                    ),
                    "strategy_variant_hash": str(trial["strategy_variant_hash"]),
                    "strategy_variant_id": str(trial["strategy_variant_id"]),
                    "status": result.status,
                    "trade_count": trading["oos_trade_count"],
                    "trial_id": trial_id,
                    "validation_artifact_paths": dict(result.validation_artifact_paths),
                }
            )
        return rows

    def _append_trial_audit_records(
        self,
        *,
        audit_log: ResearchAuditLog,
        generation_index: int,
        trial_evidence_rows: Sequence[Mapping[str, Any]],
    ) -> None:
        for trial_index, row in enumerate(trial_evidence_rows):
            audit_log.append(
                "research_run_completed",
                {
                    "event": "autonomous_trial_recorded",
                    "evidence_bundle_id": row.get("evidence_bundle_id"),
                    "generation_id": row["generation_id"],
                    "manifest_hash": row["manifest_hash"],
                    "status": row["status"],
                    "trial_id": row["trial_id"],
                },
                created_at=datetime(2026, 5, 26, tzinfo=UTC)
                + timedelta(seconds=(generation_index * 100) + trial_index),
            )

    def _select_generation_candidates(
        self,
        *,
        run: AutonomousResearchRun,
        generation_id: str,
        trials: Sequence[Mapping[str, Any]],
        trial_results: Sequence[ResearchTrialResult],
        trial_evidence_rows: Sequence[Mapping[str, Any]],
        evidence_registry: EvidenceRegistry,
        audit_log: ResearchAuditLog,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        selected_rows: list[dict[str, Any]] = []
        rejected_rows: list[dict[str, Any]] = []
        trial_by_id = {str(trial["trial_id"]): trial for trial in trials}
        result_by_id = {result.trial_id: result for result in trial_results}
        row_by_id = {str(row["trial_id"]): dict(row) for row in trial_evidence_rows}

        selector_inputs = [
            self._selector_candidate(
                row=row_by_id[str(trial["trial_id"])],
                trial=trial,
                trial_result=result_by_id[str(trial["trial_id"])],
            )
            for trial in trials
        ]
        selection = CandidateSelector(self._selection_policy(run)).select(
            selector_inputs,
            metrics_schema=self._metrics_schema(),
        )
        selection_dir = run.output_root / generation_id / "selection"
        selection.write_artifacts(selection_dir)
        self._write_jsonl(selection_dir / "candidate_results.jsonl", selector_inputs)
        audit_log.append(
            "selection_completed",
            selection.to_payload(),
            created_at=datetime(2026, 5, 26, tzinfo=UTC) + timedelta(seconds=250),
        )

        for rejected in selection.rejected_candidates:
            row = row_by_id[rejected.candidate_id]
            rejected_rows.append(
                {
                    **row,
                    "gauntlet_reasons": [],
                    "reasons": list(rejected.reasons),
                    "rejection_stage": "selector",
                    "selector_reasons": list(rejected.reasons),
                }
            )

        gauntlet_results: list[dict[str, Any]] = []
        validation_runner = ResearchExperimentRunner(repo_root=self._repo_root)
        for selected in selection.selected_candidates:
            trial_id = selected.candidate_id
            row = row_by_id[trial_id]
            result = result_by_id[trial_id]
            trial = trial_by_id[trial_id]
            metrics = self._mapping(row["metrics"], "metrics")
            validation_artifact_paths = validation_runner.write_validation_artifacts_for_trial(
                trial=trial,
                trial_result=result,
            )
            result = replace(result, validation_artifact_paths=validation_artifact_paths)
            result_by_id[trial_id] = result
            row = {
                **row,
                "validation_artifact_paths": dict(validation_artifact_paths),
            }
            row_by_id[trial_id] = row
            candidate_payload = {
                **dict(selected.candidate_payload),
                "validation": self._validation_payload_from_artifacts(validation_artifact_paths),
            }
            gauntlet = self._validation_gauntlet(run).validate(
                candidate_payload,
                audit_log=audit_log,
                created_at=datetime(2026, 5, 26, tzinfo=UTC) + timedelta(seconds=300),
            )
            gauntlet_results.append(gauntlet.to_payload())
            if not gauntlet.accepted:
                rejected_rows.append(
                    {
                        **row,
                        "gauntlet_reasons": list(gauntlet.reasons),
                        "reasons": list(gauntlet.reasons),
                        "rejection_stage": "gauntlet",
                        "selector_reasons": [],
                    }
                )
                continue
            bundle = evidence_registry.create_from_workflow_summary(
                result.metrics_path.parent / "workflow_summary.json",
                idea=self._idea(run, generation_id, trial),
                strategy_id=f"{run.campaign_id}_strategy",
                audit_log=audit_log,
                artifact_graph_writer=ResearchArtifactGraphWriter(
                    run.output_root / "artifact_graph"
                ),
            )
            bundle_verification = evidence_registry.verify(
                bundle.evidence_bundle_id,
                audit_log=audit_log,
            )
            if not bundle_verification.accepted:
                rejected_rows.append(
                    {
                        **row,
                        "gauntlet_reasons": [],
                        "promotion_reasons": list(bundle_verification.reasons),
                        "reasons": list(bundle_verification.reasons),
                        "rejection_stage": "promotion_packet",
                        "selector_reasons": [],
                    }
                )
                continue
            packet_payload = self._promotion_packet_payload(
                run=run,
                generation_id=generation_id,
                trial=trial,
                trial_result=result,
                evidence_bundle_id=bundle.evidence_bundle_id,
                metrics_payload=metrics,
            )
            packet = PromotionPacketV2.from_payload(packet_payload)
            validation = packet.validate_machine(
                evidence_registry=evidence_registry,
                audit_log=audit_log,
                artifact_graph_writer=ResearchArtifactGraphWriter(
                    run.output_root / "artifact_graph"
                ),
            )
            packet_path = run.output_root / "packets" / f"{packet.promotion_candidate_id}.json"
            self._write_json(
                packet_path,
                {
                    **packet.to_payload(),
                    "audit_record_id": validation.audit_record_id,
                    "packet_hash": validation.packet_hash,
                    "validation": validation.to_payload(),
                },
            )
            if validation.accepted:
                selected_rows.append(
                    {
                        **dict(row),
                        "evidence_bundle_id": bundle.evidence_bundle_id,
                        "packet_hash": validation.packet_hash,
                        "promotion_candidate_id": packet.promotion_candidate_id,
                        "promotion_packet_path": str(packet_path),
                        "promotion_status": validation.status,
                        "validation_audit_record_id": validation.audit_record_id,
                    }
                )
            else:
                rejected_rows.append(
                    {
                        **row,
                        "gauntlet_reasons": [],
                        "promotion_reasons": list(validation.reasons),
                        "reasons": list(validation.reasons),
                        "rejection_stage": "promotion_packet",
                        "selector_reasons": [],
                    }
                )
        self._write_json(
            run.output_root / generation_id / "validation_gauntlet.json",
            {"results": gauntlet_results},
        )
        return selected_rows, rejected_rows

    def _selector_candidate(
        self,
        *,
        row: Mapping[str, Any],
        trial: Mapping[str, Any],
        trial_result: ResearchTrialResult,
    ) -> dict[str, Any]:
        return {
            "candidate_id": str(row["trial_id"]),
            "candidate_space_hash": row["candidate_space_hash"],
            "data_quality": json.loads(trial_result.data_quality_path.read_text(encoding="utf-8")),
            "evidence": {
                "evidence_bundle_id": row.get("evidence_bundle_id"),
                "manifest_hash": row["manifest_hash"],
                "metrics_path": row["metrics_path"],
            },
            "metrics": dict(self._mapping(row["metrics"], "metrics")),
            "parameters": dict(self._mapping(trial["parameters"], "parameters")),
            "reproducibility": json.loads(
                trial_result.reproducibility_path.read_text(encoding="utf-8")
            ),
            "validation": self._validation_payload_from_artifacts(
                trial_result.validation_artifact_paths
            ),
        }

    def _validation_payload_from_artifacts(
        self,
        validation_artifact_paths: Mapping[str, str],
    ) -> dict[str, Any]:
        if not validation_artifact_paths:
            return {"artifacts": {}}
        artifacts: dict[str, dict[str, str]] = {}
        for artifact_name, path_text in sorted(validation_artifact_paths.items()):
            path = Path(path_text)
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, Mapping):
                raise ValueError(f"validation artifact must be a JSON object: {path}")
            payload_hash = payload.get("payload_hash")
            if not isinstance(payload_hash, str) or not payload_hash.strip():
                raise ValueError(f"validation artifact missing payload_hash: {path}")
            artifacts[artifact_name] = {"path": str(path), "payload_hash": payload_hash}
        return {"artifacts": artifacts, "evidence_mode": "artifact"}

    def _metrics_from_trial_result(self, result: ResearchTrialResult) -> Mapping[str, Any]:
        payload = json.loads(result.metrics_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"trial metrics artifact must be a JSON object: {result.metrics_path}")
        return dict(payload)

    def _candidate_parameter_rows_from_trials(
        self,
        trials: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "candidate_id": str(trial["candidate_id"]),
                "candidate_space_hash": str(trial["candidate_space_hash"]),
                "family": str(trial["family"]),
                "parameters": dict(self._mapping(trial["parameters"], "parameters")),
                "proposal_application": dict(
                    self._mapping(trial.get("proposal_application", {}), "proposal_application")
                ),
                "strategy_variant_hash": str(trial["strategy_variant_hash"]),
                "strategy_variant_id": str(trial["strategy_variant_id"]),
                "trial_id": str(trial["trial_id"]),
            }
            for trial in trials
        )

    def _candidate_parameter_rows_from_trial_evidence(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "candidate_id": str(row["candidate_id"]),
                "candidate_space_hash": str(row["candidate_space_hash"]),
                "family": str(row["family"]),
                "generation_id": str(row["generation_id"]),
                "parameters": dict(self._mapping(row["parameters"], "parameters")),
                "proposal_application": dict(
                    self._mapping(row.get("proposal_application", {}), "proposal_application")
                ),
                "strategy_variant_hash": str(row["strategy_variant_hash"]),
                "strategy_variant_id": str(row["strategy_variant_id"]),
                "trial_id": str(row["trial_id"]),
            }
            for row in rows
        )

    def _selection_policy(self, run: AutonomousResearchRun) -> SelectionPolicy:
        constraints = self._constraint_payload(run)
        return SelectionPolicy(
            max_drawdown=float(constraints.get("max_drawdown", 0.25)),
            min_oos_trade_count=int(constraints.get("min_oos_trade_count", 30)),
            max_selected=1,
            total_return_metric="performance.total_return",
            oos_sharpe_metric="performance.oos_sharpe",
            max_drawdown_metric="performance.max_drawdown",
            oos_trade_count_metric="trading.oos_trade_count",
            purpose="promotion",
            cost_sensitivity_metric="costs.cost_sensitivity",
        )

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
            require_artifacts=True,
        )

    def _append_landscape_points(
        self,
        *,
        run: AutonomousResearchRun,
        landscape_store: FitnessLandscapeStore,
        rows: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        payloads: list[dict[str, Any]] = []
        for row in rows:
            parameters = self._mapping(row["parameters"], "parameters")
            metrics = (
                self._planner_metrics(self._mapping(row["metrics"], "metrics"))
                if isinstance(row.get("metrics"), Mapping)
                else {}
            )
            accepted = "promotion_candidate_id" in row
            evidence_bundle_id = (
                None if row.get("evidence_bundle_id") is None else str(row["evidence_bundle_id"])
            )
            lifecycle_status = self._landscape_lifecycle_status(row, accepted=accepted)
            point = FitnessLandscapePoint(
                trial_id=str(row["trial_id"]),
                retry_id=None,
                campaign_id=run.campaign_id,
                generation_id=str(row["generation_id"]),
                strategy_family=str(row["family"]),
                factor_family=str(row["factor_family"]),
                universe=run.universe,
                root=str(parameters.get("root", run.universe[0])),
                timeframe=run.timeframe,
                regime=str(parameters.get("regime", "research")),
                session=str(parameters.get("session", "rth")),
                parameter_hash=stable_json_hash(parameters),
                metrics=metrics,
                constraints=self._constraint_payload(run),
                accepted=accepted,
                rejected_reasons=tuple(str(reason) for reason in row.get("reasons", ())),
                evidence_bundle_id=evidence_bundle_id,
                promotion_packet_id=(str(row["promotion_candidate_id"]) if accepted else None),
                artifact_graph_hash=stable_json_hash(
                    {
                        "parameter_hash": stable_json_hash(parameters),
                        "trial_id": row["trial_id"],
                    }
                ),
                lifecycle_status=lifecycle_status,
                rejection_stage=(
                    None
                    if accepted or row.get("rejection_stage") is None
                    else str(row["rejection_stage"])
                ),
            )
            landscape_store.append(point)
            payloads.append(point.to_payload())
        return tuple(payloads)

    @staticmethod
    def _landscape_lifecycle_status(row: Mapping[str, Any], *, accepted: bool) -> str:
        if accepted:
            return "selected"
        stage = str(row.get("rejection_stage") or row.get("stage") or "").strip()
        if stage == "trial_budget":
            return "budget_rejected"
        if stage == "selector":
            return "selector_rejected"
        if stage == "gauntlet":
            return "gauntlet_rejected"
        if stage == "promotion_packet":
            return "promotion_packet_rejected"
        if row.get("status") == "failed":
            return "execution_failed"
        return "execution_rejected"

    @staticmethod
    def _planner_metrics(metrics: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in metrics.items()
            if key not in {"backtest", "backtest_metrics", "backtest_statistics"}
        }

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

    def _next_generation_proposal(
        self,
        *,
        run: AutonomousResearchRun,
        previous_generation_id: str,
        analytics: FitnessAnalytics,
        accepted_trial_count: int,
        data_window: Mapping[str, str],
    ) -> NextGenerationProposal:
        next_generation_number = int(previous_generation_id.rsplit("-", maxsplit=1)[1]) + 1
        remaining_trials = max(0, self._max_total_trials(run) - accepted_trial_count)
        requested_trials = min(run.trials_per_generation, remaining_trials)
        return NextGenerationProposal.from_analytics(
            campaign_id=run.campaign_id,
            previous_generation_id=previous_generation_id,
            next_generation_id=f"generation-{next_generation_number:03d}",
            analytics=analytics,
            previous_campaign_config={"data_window": dict(data_window)},
            trial_budget_state={
                "remaining_trials": remaining_trials,
                "requested_trials": requested_trials,
            },
            human_constraints={"max_trials_per_generation": run.trials_per_generation},
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

    def _yaml_mapping(self, path: Path) -> Mapping[str, Any]:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if raw is None:
            return {}
        if not isinstance(raw, Mapping):
            raise ValueError(f"YAML config must be a mapping: {path}")
        return dict(raw)

    def _promotion_packet_payload(
        self,
        *,
        run: AutonomousResearchRun,
        generation_id: str,
        trial: Mapping[str, Any],
        trial_result: ResearchTrialResult,
        evidence_bundle_id: str,
        metrics_payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        data_quality_payload = json.loads(
            trial_result.data_quality_path.read_text(encoding="utf-8")
        )
        reproducibility_payload = json.loads(
            trial_result.reproducibility_path.read_text(encoding="utf-8")
        )
        promotion_candidate_id = f"pc-{generation_id}-{trial['trial_id']}"
        return {
            "data_quality": {
                "artifact_id": data_quality_payload.get("artifact_id", trial_result.trial_id),
                "payload": data_quality_payload,
                "payload_hash": stable_json_hash(data_quality_payload),
            },
            "evidence_bundle_id": evidence_bundle_id,
            "idea_id": self._idea(run, generation_id, trial).idea_id,
            "metrics": {
                "metrics_schema_id": "schema_v2",
                "payload": dict(metrics_payload),
                "payload_hash": stable_json_hash(metrics_payload),
            },
            "operations": {
                "alert_policy": "research-only alert projection",
                "monitoring_plan": "research-only monitoring projection",
                "rollback_plan": "research-only rollback projection",
            },
            "promotion_candidate_id": promotion_candidate_id,
            "reproducibility": {
                "payload": reproducibility_payload,
                "payload_hash": stable_json_hash(reproducibility_payload),
                "snapshot_id": reproducibility_payload.get("artifact_id", trial_result.trial_id),
            },
            "review": {
                "status": "human_pending",
            },
            "runtime": {
                "account_id": "research-only",
                "capital_limit": 0,
                "kill_switch_profile": "research-only",
                "risk_profile_id": "research-only",
                "runtime_mode": "paper_simulated",
            },
            "schema_version": 2,
            "source_module": f"strategies.research.{run.campaign_id}",
            "strategy_id": f"{run.campaign_id}_strategy",
            "target_mode": "paper_simulated",
            "target_module": f"strategies.production.{run.campaign_id}",
        }

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

    def _write_final_artifact_graph(
        self,
        *,
        root: Path,
        selected_rows: Sequence[Mapping[str, Any]],
        report_path: Path,
        audit_log: ResearchAuditLog,
    ) -> Path:
        if not selected_rows:
            raise ValueError("artifact graph requires at least one selected candidate")
        graph_path = root / "artifact_graph" / "artifact_graph.json"
        report_hash = self._sha256_path(report_path)
        graph = self._merged_selected_artifact_graph(
            artifact_graph_hash="sha256:artifact-graph",
            artifact_graph_path=graph_path,
            audit_log=audit_log,
            report_hash=report_hash,
            report_path=report_path,
            root=root,
            selected_rows=selected_rows,
        )
        graph = self._merged_selected_artifact_graph(
            artifact_graph_hash=graph.stable_hash(),
            artifact_graph_path=graph_path,
            audit_log=audit_log,
            report_hash=report_hash,
            report_path=report_path,
            root=root,
            selected_rows=selected_rows,
        )
        graph.validate_full_chain()
        self._write_json(graph_path, graph.to_payload())
        return graph_path

    def _merged_selected_artifact_graph(
        self,
        *,
        artifact_graph_hash: str,
        artifact_graph_path: Path,
        audit_log: ResearchAuditLog,
        report_hash: str,
        report_path: Path,
        root: Path,
        selected_rows: Sequence[Mapping[str, Any]],
    ) -> ResearchArtifactGraph:
        nodes: dict[str, ResearchArtifactNode] = {}
        edges: set[tuple[str, str, str]] = set()
        registry = EvidenceRegistry(root / "evidence")
        for selected in selected_rows:
            packet_payload = json.loads(
                Path(str(selected["promotion_packet_path"])).read_text(encoding="utf-8")
            )
            bundle = registry.show(str(selected["evidence_bundle_id"]))
            audit_record = self._audit_record(
                audit_log,
                str(selected["validation_audit_record_id"]),
            )
            manifest_path = bundle.manifest_paths[0]
            manifest_hashes = cast(Mapping[str, str], bundle.manifest_hashes or {})
            graph = self._artifact_graph(
                artifact_graph_hash=artifact_graph_hash,
                artifact_graph_path=artifact_graph_path,
                audit_payload_hash=audit_record.payload_hash,
                audit_record_id=audit_record.record_id,
                bundle_payload=bundle.to_payload(),
                data_quality_hash=str(packet_payload["data_quality"]["payload_hash"]),
                data_quality_path=str(
                    packet_payload["data_quality"]["payload"].get("path", "data_quality")
                ),
                manifest_hash=str(manifest_hashes[manifest_path]),
                manifest_path=manifest_path,
                metrics_hash=str(packet_payload["metrics"]["payload_hash"]),
                metrics_path=str(selected["metrics_path"]),
                packet_hash=str(packet_payload["packet_hash"]),
                promotion_candidate_id=str(packet_payload["promotion_candidate_id"]),
                report_hash=report_hash,
                report_path=report_path,
                reproducibility_hash=str(packet_payload["reproducibility"]["payload_hash"]),
                reproducibility_path=str(
                    packet_payload["reproducibility"]["payload"].get(
                        "path",
                        packet_payload["reproducibility"].get(
                            "snapshot_id",
                            "reproducibility",
                        ),
                    )
                ),
                strategy_variant_hash=str(selected["strategy_variant_hash"]),
                strategy_variant_id=str(selected["strategy_variant_id"]),
            )
            for node in graph.nodes:
                existing = nodes.get(node.node_id)
                if (
                    existing is not None
                    and existing != node
                    and not self._same_artifact_node(existing, node)
                ):
                    raise ValueError(f"conflicting artifact graph node: {node.node_id}")
                if existing is None:
                    nodes[node.node_id] = node
            for edge in graph.edges:
                edges.add((edge.source_id, edge.target_id, edge.relation))
        return ResearchArtifactGraph(
            nodes=tuple(nodes.values()),
            edges=tuple(
                ResearchArtifactEdge(source_id=source, target_id=target, relation=relation)
                for source, target, relation in sorted(edges)
            ),
        )

    @staticmethod
    def _same_artifact_node(left: ResearchArtifactNode, right: ResearchArtifactNode) -> bool:
        return left.node_type == right.node_type and left.payload_hash == right.payload_hash

    def _write_empty_artifact_graph(self, root: Path) -> Path:
        graph_path = root / "artifact_graph" / "artifact_graph.json"
        self._write_json(graph_path, ResearchArtifactGraph().to_payload())
        return graph_path

    def _write_next_generation_proposal(
        self,
        path: Path,
        proposal: NextGenerationProposal,
    ) -> None:
        payload = proposal.to_payload()
        evidence_refs = sorted(
            {
                ref
                for mutation in proposal.mutations
                for ref in mutation.evidence_refs
                if ref.strip()
            }
        )
        self._write_json(
            path,
            {
                **payload,
                "approval_policy": "manual_gate",
                "evidence_refs": evidence_refs,
                "generation_id": proposal.next_generation_id,
                "requires_human_approval": True,
                "status": "pending_human_approval",
                "trial_budget_state": {
                    "max_trials": proposal.max_trial_budget,
                    "remaining_trials": proposal.max_trial_budget,
                    "requested_trials": proposal.trial_budget,
                },
            },
        )

    def _artifact_graph(
        self,
        *,
        artifact_graph_hash: str,
        artifact_graph_path: Path,
        audit_payload_hash: str,
        audit_record_id: str,
        bundle_payload: Mapping[str, Any],
        data_quality_hash: str,
        data_quality_path: str,
        manifest_hash: str,
        manifest_path: str,
        metrics_hash: str,
        metrics_path: str,
        packet_hash: str,
        promotion_candidate_id: str,
        report_hash: str,
        report_path: Path,
        reproducibility_hash: str,
        reproducibility_path: str,
        strategy_variant_hash: str,
        strategy_variant_id: str,
    ) -> ResearchArtifactGraph:
        evidence_bundle_id = str(bundle_payload["evidence_bundle_id"])
        workflow_run_id = str(bundle_payload["workflow_run_id"])
        nodes = (
            ResearchArtifactNode(manifest_path, "manifest", manifest_hash),
            ResearchArtifactNode(
                workflow_run_id,
                "workflow_run",
                stable_json_hash({"workflow_run_id": workflow_run_id}),
            ),
            ResearchArtifactNode(
                evidence_bundle_id,
                "evidence_bundle",
                stable_json_hash(bundle_payload),
            ),
            ResearchArtifactNode(
                strategy_variant_id,
                "strategy_variant",
                strategy_variant_hash,
                metadata={"promotion_candidate_id": promotion_candidate_id},
            ),
            ResearchArtifactNode(metrics_path, "metrics", metrics_hash),
            ResearchArtifactNode(data_quality_path, "data_quality", data_quality_hash),
            ResearchArtifactNode(reproducibility_path, "reproducibility", reproducibility_hash),
            ResearchArtifactNode(promotion_candidate_id, "promotion_packet", packet_hash),
            ResearchArtifactNode(audit_record_id, "audit_record", audit_payload_hash),
            ResearchArtifactNode(str(report_path), "report", report_hash),
            ResearchArtifactNode(str(artifact_graph_path), "artifact_graph", artifact_graph_hash),
        )
        edges = (
            ResearchArtifactEdge(workflow_run_id, manifest_path, "references"),
            ResearchArtifactEdge(evidence_bundle_id, manifest_path, "references"),
            ResearchArtifactEdge(evidence_bundle_id, metrics_path, "references"),
            ResearchArtifactEdge(evidence_bundle_id, data_quality_path, "references"),
            ResearchArtifactEdge(evidence_bundle_id, reproducibility_path, "references"),
            ResearchArtifactEdge(promotion_candidate_id, evidence_bundle_id, "references"),
            ResearchArtifactEdge(promotion_candidate_id, strategy_variant_id, "references"),
            ResearchArtifactEdge(promotion_candidate_id, metrics_path, "references"),
            ResearchArtifactEdge(promotion_candidate_id, data_quality_path, "references"),
            ResearchArtifactEdge(promotion_candidate_id, reproducibility_path, "references"),
            ResearchArtifactEdge(promotion_candidate_id, audit_record_id, "references"),
            ResearchArtifactEdge(str(report_path), promotion_candidate_id, "references"),
            ResearchArtifactEdge(str(report_path), audit_record_id, "references"),
            ResearchArtifactEdge(str(report_path), str(artifact_graph_path), "references"),
        )
        return ResearchArtifactGraph(nodes=nodes, edges=edges)

    def _audit_record(self, audit_log: ResearchAuditLog, record_id: str) -> Any:
        for record in audit_log.list():
            if record.record_id == record_id:
                return record
        raise ValueError(f"audit record not found: {record_id}")

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
            edge_type=self._edge_type(family),
            source="autonomous_research_engine",
            created_at=datetime(2026, 5, 26, tzinfo=UTC),
        )

    def _edge_type(self, family: str) -> str:
        allowed = {
            "carry",
            "cross_sectional_momentum",
            "event_driven",
            "execution_alpha",
            "liquidity",
            "macro",
            "macro_regime",
            "mean_reversion",
            "microstructure",
            "momentum",
            "quality",
            "relative_value",
            "reversal",
            "seasonality",
            "sentiment",
            "term_structure",
            "time_series_momentum",
            "value",
            "volatility",
        }
        if family in allowed:
            return family
        if family == "spread":
            return "relative_value"
        if family == "breakout":
            return "time_series_momentum"
        return "momentum"

    def _write_report(
        self,
        path: Path,
        *,
        campaign_id: str,
        selected_count: int,
        rejected_count: int,
    ) -> None:
        path.write_text(
            "\n".join(
                [
                    f"# {campaign_id} Research Acceptance",
                    "",
                    f"selected_candidates: {selected_count}",
                    f"rejected_candidates: {rejected_count}",
                    "paper_live_launches: 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")

    def _write_jsonl(self, path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(dict(row), sort_keys=True) for row in rows]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def _sha256_path(self, path: Path) -> str:
        return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"

    def _mapping(self, value: Any, field_name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return dict(value)


__all__ = [
    "AutonomousResearchEngine",
    "AutonomousResearchGeneration",
    "AutonomousResearchResult",
    "AutonomousResearchRun",
]
