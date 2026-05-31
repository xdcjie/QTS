"""Autonomous research campaign + trial orchestration.

Stateless orchestration functions (campaign loop, generation/trial execution, candidate
selection, backtest-config materialization, evidence projection, and promotion-packet
assembly) extracted from AutonomousResearchEngine (QTS-FINAL-011). Each takes an
AutonomousResearchCampaignSupport for evidence/config resolution and campaign state.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import (
    ResearchArtifactGraphWriter,
)
from qts.research.audit_log import ResearchAuditLog
from qts.research.campaign import ResearchCampaignFamily
from qts.research.engine.autonomous_campaign_support import AutonomousResearchCampaignSupport
from qts.research.engine.autonomous_engine_helpers import (
    _active_correlation_context,
    _active_correlation_context_from_selected,
    _append_trial_audit_records,
    _backtest_pipeline_template,
    _candidate_parameter_rows_from_trial_evidence,
    _candidate_parameter_rows_from_trials,
    _ensure_full_backtest_csv,
    _family_candidate_budget,
    _landscape_lifecycle_status,
    _mapping,
    _materialize_backtest_csv,
    _materialized_contract_symbol_resolver,
    _metrics_from_trial_result,
    _ordered_family_specs,
    _parameter_space_payload,
    _parse_timestamp,
    _planner_metrics,
    _proposal_adjusted_template,
    _proposal_application_payload,
    _proposal_manifest_patch,
    _round_robin_candidates,
    _selector_candidate,
    _strategy_parameter_bindings,
    _validation_payload_from_artifacts,
    _write_empty_artifact_graph,
    _write_final_artifact_graph,
    _write_json,
    _write_jsonl,
    _write_next_generation_proposal,
    _write_report,
    _yaml_mapping,
)
from qts.research.engine.autonomous_research_types import (
    AutonomousResearchGeneration,
    AutonomousResearchResult,
    AutonomousResearchRun,
)
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.factory.strategy_template import StrategyTemplate, StrategyVariantFactory
from qts.research.landscape import FitnessAnalytics, FitnessLandscapePoint, FitnessLandscapeStore
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentRunner,
    ResearchTrialResult,
)
from qts.research.planner import (
    NextGenerationProposal,
)
from qts.research.promotion_packet import PromotionPacketV2
from qts.research.search import (
    CandidateGenerator,
    SearchSpaceSpec,
    TrialBudgetManager,
)
from qts.research.selector import (
    CandidateSelector,
)


def run(
    support: AutonomousResearchCampaignSupport, run: AutonomousResearchRun
) -> AutonomousResearchResult:
    """Run a bounded autonomous campaign without launching runtime modes."""

    root = run.output_root
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    _write_json(root / "campaign_config.json", run.to_payload())
    data_paths = support._required_data_paths(run)
    audit_log = ResearchAuditLog(root / "audit" / "audit_log.jsonl")
    evidence_registry = EvidenceRegistry(root / "evidence")
    landscape_store = FitnessLandscapeStore(root / "fitness_landscape.jsonl")
    budget_manager = support._budget_manager(run, root)

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
            approval_payload = support._generation_approval_payload(run, next_proposal)
            audit_log.append(
                "generation_approval_decided",
                approval_payload,
                created_at=datetime(2026, 5, 26, tzinfo=UTC) + timedelta(seconds=generation_index),
            )
            if approval_payload["accepted"] is not True:
                stop_status = "pending_human_approval"
                approval_reasons = tuple(str(reason) for reason in approval_payload["reasons"])
                break
            active_proposal = next_proposal
        generation = _run_generation(
            support,
            run=run,
            generation_index=generation_index,
            proposal=active_proposal,
            data_paths=data_paths,
            audit_log=audit_log,
            evidence_registry=evidence_registry,
            landscape_store=landscape_store,
            budget_manager=budget_manager,
            active_selected_rows=tuple(selected_rows),
        )
        generations.append(generation["generation"])
        all_trial_evidence_rows.extend(generation["trial_evidence_rows"])
        selected_rows.extend(generation["selected_rows"])
        rejected_rows.extend(generation["rejected_rows"])
        next_proposal = cast(NextGenerationProposal, generation["next_generation_proposal"])

    fitness_landscape_path = root / "fitness_landscape.jsonl"
    selected_candidates_path = root / "selected_candidates.jsonl"
    rejected_candidates_path = root / "rejected_candidates.jsonl"
    _write_jsonl(selected_candidates_path, selected_rows)
    _write_jsonl(rejected_candidates_path, rejected_rows)

    fitness_analytics_path = root / "fitness_analytics.json"
    analytics = FitnessAnalytics.from_landscape(landscape_store.read())
    _write_json(fitness_analytics_path, analytics.to_payload())
    next_generation_proposal_path = root / "next_generation_proposal.json"
    if next_proposal is None:
        _write_json(next_generation_proposal_path, {})
    else:
        _write_next_generation_proposal(next_generation_proposal_path, next_proposal)
    _write_jsonl(
        root / "candidate_parameters.jsonl",
        _candidate_parameter_rows_from_trial_evidence(all_trial_evidence_rows),
    )

    report_path = root / "report.md"
    _write_report(
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
    _write_json(validation_summary_path, validation_summary)
    artifact_graph_path = (
        _write_final_artifact_graph(
            root=root,
            selected_rows=selected_rows,
            report_path=report_path,
            audit_log=audit_log,
        )
        if selected_rows
        else _write_empty_artifact_graph(root)
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
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    generation_index: int,
    proposal: NextGenerationProposal | None,
    data_paths: Mapping[str, Path],
    audit_log: ResearchAuditLog,
    evidence_registry: EvidenceRegistry,
    landscape_store: FitnessLandscapeStore,
    budget_manager: TrialBudgetManager,
    active_selected_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    generation_id = f"generation-{generation_index:03d}"
    generation_dir = run.output_root / generation_id
    generation_dir.mkdir(parents=True, exist_ok=True)
    budget_rejected_rows: list[dict[str, Any]] = []
    trials = _trials(
        support,
        run,
        generation_id,
        generation_index,
        proposal=proposal,
        budget_manager=budget_manager,
        audit_log=audit_log,
        budget_rejected_rows=budget_rejected_rows,
    )
    _write_jsonl(
        generation_dir / "candidate_parameters.jsonl",
        _candidate_parameter_rows_from_trials(trials),
    )
    checked_paths = tuple(str(path) for path in data_paths.values())
    job = ResearchExperimentJob(
        job_id=f"{run.campaign_id}-{generation_id}",
        generation_id=generation_id,
        manifest_payload=_manifest_payload(support, run, checked_paths, data_paths),
        output_root=run.output_root,
        trials=trials,
    )
    experiment_result = support._run_experiment_job(job, audit_log=audit_log)
    trial_evidence_rows = _trial_evidence_rows(
        support,
        run=run,
        generation_id=generation_id,
        trials=trials,
        trial_results=experiment_result.trials,
    )
    _append_trial_audit_records(
        audit_log=audit_log,
        generation_index=generation_index,
        trial_evidence_rows=trial_evidence_rows,
    )
    selected_rows, execution_rejected_rows = _select_generation_candidates(
        support,
        run=run,
        generation_id=generation_id,
        trials=trials,
        trial_results=experiment_result.trials,
        trial_evidence_rows=trial_evidence_rows,
        evidence_registry=evidence_registry,
        audit_log=audit_log,
        active_selected_rows=active_selected_rows,
    )
    rejected_rows = [*execution_rejected_rows, *budget_rejected_rows]
    generation_landscape_rows = _append_landscape_points(
        support,
        run=run,
        landscape_store=landscape_store,
        rows=(*selected_rows, *execution_rejected_rows, *budget_rejected_rows),
    )
    landscape_path = generation_dir / "fitness_landscape.jsonl"
    proposal_path = generation_dir / "next_generation_proposal.json"
    _write_jsonl(landscape_path, generation_landscape_rows)
    next_proposal = _next_generation_proposal(
        support,
        run=run,
        previous_generation_id=generation_id,
        analytics=FitnessAnalytics.from_landscape(landscape_store.read()),
        accepted_trial_count=len(landscape_store.read().points),
        data_window=support._combined_data_window(
            tuple(data_paths.values()),
            max_rows=support._materialization_max_rows(run),
        ),
    )
    _write_next_generation_proposal(proposal_path, next_proposal)
    audit_log.append(
        "next_generation_proposed",
        next_proposal.to_payload(),
        created_at=datetime(2026, 5, 26, tzinfo=UTC) + timedelta(seconds=500 + generation_index),
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


def _select_generation_candidates(
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    generation_id: str,
    trials: Sequence[Mapping[str, Any]],
    trial_results: Sequence[ResearchTrialResult],
    trial_evidence_rows: Sequence[Mapping[str, Any]],
    evidence_registry: EvidenceRegistry,
    audit_log: ResearchAuditLog,
    active_selected_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    trial_by_id = {str(trial["trial_id"]): trial for trial in trials}
    result_by_id = {result.trial_id: result for result in trial_results}
    row_by_id = {str(row["trial_id"]): dict(row) for row in trial_evidence_rows}

    # Validation artifacts must exist before selection: the selector enforces
    # the promotion metrics schema, and the artifact-derived fields
    # (deterministic_replay_passed, no_lookahead_passed, walk_forward
    # consistency, parameter_sensitivity, oos_months, promotion_eligible)
    # are honestly None until the survivor validation runs have produced the
    # artifacts the metrics are derived from. Producing them up front keeps
    # selection driven by real evidence rather than rejecting every
    # candidate for missing-but-not-yet-derived fields.
    validation_runner = ResearchExperimentRunner(
        repo_root=support._repo_root,
        promotion_thresholds=support._promotion_thresholds(run),
    )
    active_correlation_context = [
        _active_correlation_context_from_selected(row) for row in active_selected_rows
    ]
    for trial in trials:
        trial_id = str(trial["trial_id"])
        result = result_by_id[trial_id]
        if result.status != "succeeded":
            continue
        validation_artifact_paths = validation_runner.write_validation_artifacts_for_trial(
            trial=trial,
            trial_result=result,
            active_correlation_context=active_correlation_context,
        )
        result_by_id[trial_id] = replace(
            result, validation_artifact_paths=validation_artifact_paths
        )
        row_by_id[trial_id] = {
            **row_by_id[trial_id],
            "metrics": dict(_metrics_from_trial_result(result_by_id[trial_id])),
            "validation_artifact_paths": dict(validation_artifact_paths),
        }

    selector_inputs = [
        _selector_candidate(
            row=row_by_id[str(trial["trial_id"])],
            trial=trial,
            trial_result=result_by_id[str(trial["trial_id"])],
        )
        for trial in trials
    ]
    # Multiple-testing correction: the multiplicity haircut must see how many
    # configurations were tried this generation, not the default of 1 (which
    # makes the expected-maximum-Sharpe haircut a no-op). Every selector input
    # is one configuration tried, so the trial count is their cardinality and
    # the scope is the generation the candidates were produced in.
    selection = CandidateSelector(support._selection_policy(run)).select(
        selector_inputs,
        metrics_schema=support._metrics_schema(),
        trial_count=max(len(selector_inputs), 1),
        multiplicity_scope="generation",
    )
    selection_dir = run.output_root / generation_id / "selection"
    selection.write_artifacts(selection_dir)
    _write_jsonl(selection_dir / "candidate_results.jsonl", selector_inputs)
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
    for selected in selection.selected_candidates:
        trial_id = selected.candidate_id
        row = row_by_id[trial_id]
        result = result_by_id[trial_id]
        trial = trial_by_id[trial_id]
        metrics = _mapping(row["metrics"], "metrics")
        validation_artifact_paths = dict(result.validation_artifact_paths)
        candidate_payload = {
            **dict(selected.candidate_payload),
            "validation": _validation_payload_from_artifacts(validation_artifact_paths),
        }
        # The deflated-Sharpe / PBO gates read the selector's multiplicity
        # adjustment, which the raw candidate payload does not carry.
        if selected.multiplicity_adjustment is not None:
            candidate_payload["multiplicity_adjustment"] = dict(selected.multiplicity_adjustment)
        gauntlet = support._validation_gauntlet(run).validate(
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
            idea=support._idea(run, generation_id, trial),
            strategy_id=f"{run.campaign_id}_strategy",
            audit_log=audit_log,
            artifact_graph_writer=ResearchArtifactGraphWriter(run.output_root / "artifact_graph"),
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
        packet_payload = _promotion_packet_payload(
            support,
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
            artifact_graph_writer=ResearchArtifactGraphWriter(run.output_root / "artifact_graph"),
        )
        packet_path = run.output_root / "packets" / f"{packet.promotion_candidate_id}.json"
        _write_json(
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
            active_correlation_context.append(
                _active_correlation_context(
                    candidate_id=packet.promotion_candidate_id,
                    trial_result=result,
                )
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
    _write_json(
        run.output_root / generation_id / "validation_gauntlet.json",
        {"results": gauntlet_results},
    )
    return selected_rows, rejected_rows


def _trials(
    support: AutonomousResearchCampaignSupport,
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
    generated_trials = _generated_trials(
        support,
        run,
        generation_id,
        generation_index,
        proposal=proposal,
    )
    for generated_index, generated_trial in enumerate(generated_trials):
        created_at = datetime(2026, 5, 26, tzinfo=UTC) + timedelta(
            seconds=(generation_index * 1000) + generated_index
        )
        if len(trials) >= run.trials_per_generation:
            decision_reason = (
                "generation trial budget exceeded: "
                f"{len(trials)}/{run.trials_per_generation} accepted"
            )
            record = budget_manager.ledger.append_decision(
                support._trial_budget_payload(
                    run=run,
                    generation_id=generation_id,
                    trial=generated_trial,
                    accepted=False,
                    decision_reason=decision_reason,
                ),
                created_at=created_at,
            )
            audit_log.append(
                "trial_budget_decision",
                record.payload,
                created_at=record.created_at,
            )
            budget_rejected_rows.append(
                _budget_rejected_row(
                    support,
                    run=run,
                    generation_id=generation_id,
                    trial=generated_trial,
                    budget_record_id=record.record_id,
                    decision_reason=decision_reason,
                )
            )
            continue
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
            created_at=created_at,
        )
        record = budget_manager.ledger.list()[-1]
        audit_log.append(
            "trial_budget_decision",
            record.payload,
            created_at=record.created_at,
        )
        if not decision.accepted:
            budget_rejected_rows.append(
                _budget_rejected_row(
                    support,
                    run=run,
                    generation_id=generation_id,
                    trial=generated_trial,
                    budget_record_id=record.record_id,
                    decision_reason=decision.reason,
                )
            )
            continue
        trials.append(generated_trial)
    return tuple(trials)


def _generated_trials(
    support: AutonomousResearchCampaignSupport,
    run: AutonomousResearchRun,
    generation_id: str,
    generation_index: int,
    *,
    proposal: NextGenerationProposal | None,
) -> tuple[Mapping[str, Any], ...]:
    candidate_budget = support._candidate_generation_budget(run, proposal)
    family_candidates: list[tuple[Mapping[str, Any], tuple[Any, ...]]] = []
    for family in _ordered_family_specs(_family_specs(support, run), proposal):
        generator = CandidateGenerator(family["search_space"])
        candidates = generator.grid(
            budget=_family_candidate_budget(
                family_id=str(family["family_id"]),
                base_budget=candidate_budget + generation_index,
                proposal=proposal,
            )
        )
        if generation_index:
            candidates = candidates[generation_index:] or candidates
        family_candidates.append((family, candidates))
    generated: list[Mapping[str, Any]] = []
    for family, candidate in _round_robin_candidates(family_candidates):
        parameters = dict(candidate.parameters)
        template = _proposal_adjusted_template(
            cast(StrategyTemplate, family["template"]),
            proposal,
        )
        variant = StrategyVariantFactory(template).create_variant(
            parameters,
            allowed_roots=run.universe,
        )
        manifest_patch = _proposal_manifest_patch(
            variant.to_manifest_patch(),
            proposal,
        )
        ordinal = len(generated)
        trial_id = f"{generation_id}-trial-{ordinal:03d}"
        root = str(parameters.get("root", run.universe[0]))
        generated.append(
            {
                "backtest_pipeline": _backtest_pipeline_payload(
                    support,
                    run=run,
                    trial_id=trial_id,
                    root=root,
                    parameters=parameters,
                    strategy_entrypoint=variant.strategy_entrypoint,
                    manifest_patch=manifest_patch,
                ),
                "candidate_id": candidate.candidate_id,
                "candidate_space_hash": candidate.candidate_space_hash,
                "factor_family": variant.family,
                "factor_hash": variant.factor_hash,
                "family": family["family_id"],
                "idea_id": support._idea_id(run, str(family["family_id"]), proposal),
                "manifest_patch": manifest_patch,
                "parameters": parameters,
                "proposal_application": _proposal_application_payload(proposal),
                "strategy_variant_hash": variant.variant_hash,
                "strategy_variant_id": variant.variant_id,
                "trial_id": trial_id,
                "validation": {"artifacts_required": True},
            }
        )
    return tuple(generated)


def _write_backtest_data_config(
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    trial_id: str,
    root: str,
    data_path: Path,
) -> tuple[Path, Path]:
    max_rows = support._materialization_max_rows(run)
    data_root = (
        run.output_root / "backtest_data" / "full" / root
        if max_rows is None
        else run.output_root / "backtest_data" / trial_id
    )
    start, _end = support._backtest_window(run, data_path)
    chain_path, chain = support._install_future_chain(
        root=root,
        source_data_path=data_path,
        data_root=data_root,
    )
    contract_symbol_for = _materialized_contract_symbol_resolver(chain)
    materialized_symbol = contract_symbol_for(_parse_timestamp(start))
    bars_dir = data_root / "data"
    bars_dir.mkdir(parents=True, exist_ok=True)
    target_csv = bars_dir / f"{root}.csv"
    windows = support._execution_windows(run)
    window = support._execution_window(run)
    if max_rows is None:
        _ensure_full_backtest_csv(
            data_path,
            target_csv,
            symbol=materialized_symbol,
            contract_symbol_for=contract_symbol_for,
            window=window,
            windows=windows,
        )
    else:
        _materialize_backtest_csv(
            data_path,
            target_csv,
            symbol=materialized_symbol,
            contract_symbol_for=contract_symbol_for,
            max_rows=max_rows,
            window=window,
            windows=windows,
        )
    config_path = data_root / "historical.local.yaml"
    payload = {
        "historical_data": {
            "catalogs": {
                "research": {
                    "datasets": {
                        root: {
                            "asset_class": "future",
                            "bars": [{"file": target_csv.name, "timeframe": run.timeframe}],
                            "chain_file": chain_path.name,
                            "exchange": run.calendar,
                        }
                    },
                    "store": "local_csv",
                }
            },
            "stores": {
                "local_csv": {
                    "bars_dir": "data",
                    "chains_dir": "chains",
                    "root_dir": str(data_root),
                    "type": "local_csv",
                }
            },
        }
    }
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path, target_csv


def _write_backtest_config(
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    trial_id: str,
    root: str,
    strategy_entrypoint: str,
    strategy_params: Mapping[str, Any],
) -> tuple[Path, Path]:
    data_paths = support._required_data_paths(run)
    data_config_path, data_quality_path = _write_backtest_data_config(
        support,
        run=run,
        trial_id=trial_id,
        root=root,
        data_path=data_paths[root],
    )
    start, end = support._backtest_window(run, data_paths[root])
    config_path = run.output_root / "backtest_configs" / f"{trial_id}.yaml"
    payload = {
        "end": end,
        # Fill policy for promotion-grade evidence. Defaults to next_bar_open
        # (a decision at bar N fills at N+1's open); same_bar_close is
        # look-ahead, requires the optimistic waiver, and is blocked at the
        # promotion bar.
        "fill_policy": run.fill_policy,
        "optimistic_fill_waiver": run.optimistic_fill_waiver,
        "initial_cash": "1000000",
        "market_data": {
            "catalog": "research",
            "config": str(data_config_path),
            "source": "local_historical",
        },
        "risk_config": {"max_notional": "100000000"},
        "roots": [root],
        "roll_policy": {"enabled": True},
        "start": start,
        "strategy_class": strategy_entrypoint,
        "strategy_params": dict(strategy_params),
        "symbols": [root],
        "timeframe": run.timeframe,
        "warmup_bars": 0,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path, data_quality_path


def _backtest_pipeline_payload(
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    trial_id: str,
    root: str,
    parameters: Mapping[str, Any],
    strategy_entrypoint: str,
    manifest_patch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pipeline_template = _backtest_pipeline_template(manifest_patch or {})
    (
        strategy_parameter_defaults,
        strategy_parameter_map,
        strategy_parameter_names,
    ) = _strategy_parameter_bindings(
        root=root,
        parameters=parameters,
        pipeline_template=pipeline_template,
    )
    backtest_config_path, data_quality_path = _write_backtest_config(
        support,
        run=run,
        trial_id=trial_id,
        root=root,
        strategy_entrypoint=strategy_entrypoint,
        strategy_params=strategy_parameter_defaults,
    )
    payload: dict[str, Any] = {
        "backtest_config_path": str(backtest_config_path),
        "data_quality_paths": [str(data_quality_path)],
        "objective_metric": "sharpe_ratio",
        "strategy_parameter_defaults": strategy_parameter_defaults,
    }
    if strategy_parameter_map is not None:
        payload["strategy_parameter_map"] = strategy_parameter_map
    if strategy_parameter_names is not None:
        payload["strategy_parameter_names"] = strategy_parameter_names
    return payload


def _promotion_packet_payload(
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    generation_id: str,
    trial: Mapping[str, Any],
    trial_result: ResearchTrialResult,
    evidence_bundle_id: str,
    metrics_payload: Mapping[str, Any],
) -> dict[str, Any]:
    data_quality_payload = json.loads(trial_result.data_quality_path.read_text(encoding="utf-8"))
    reproducibility_payload = json.loads(
        trial_result.reproducibility_path.read_text(encoding="utf-8")
    )
    promotion_candidate_id = f"pc-{generation_id}-{trial['trial_id']}"
    return {
        "data_quality": {
            "artifact_id": data_quality_payload.get("artifact_id", trial_result.trial_id),
            "payload": {**data_quality_payload, "path": str(trial_result.data_quality_path)},
            "payload_hash": stable_json_hash(
                {**data_quality_payload, "path": str(trial_result.data_quality_path)}
            ),
        },
        "evidence_bundle_id": evidence_bundle_id,
        "idea_id": support._idea(run, generation_id, trial).idea_id,
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
            "payload": {
                **reproducibility_payload,
                "path": str(trial_result.reproducibility_path),
            },
            "payload_hash": stable_json_hash(
                {**reproducibility_payload, "path": str(trial_result.reproducibility_path)}
            ),
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


def _manifest_payload(
    support: AutonomousResearchCampaignSupport,
    run: AutonomousResearchRun,
    checked_paths: tuple[str, ...],
    data_paths: Mapping[str, Path],
) -> dict[str, Any]:
    execution = run.campaign_config.execution if run.campaign_config is not None else None
    execution_windows = support._execution_windows(run)
    data_window = (
        {"end": execution_windows[-1][1], "start": execution_windows[0][0]}
        if execution_windows
        else (
            {"end": execution.end, "start": execution.start}
            if execution is not None and execution.start is not None and execution.end is not None
            else support._combined_data_window(
                tuple(data_paths.values()),
                max_rows=support._materialization_max_rows(run),
            )
        )
    )
    data_windows = (
        [{"end": end, "start": start} for start, end in execution_windows]
        if execution_windows
        else [data_window]
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
                    None if run.campaign_config is None else run.campaign_config.execution.data_mode
                ),
                "max_rows": (
                    None if run.campaign_config is None else run.campaign_config.execution.max_rows
                ),
            },
            "start": data_window["start"],
            "timeframe": run.timeframe,
            "windows": data_windows,
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


def _append_landscape_points(
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    landscape_store: FitnessLandscapeStore,
    rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    payloads: list[dict[str, Any]] = []
    for row in rows:
        parameters = _mapping(row["parameters"], "parameters")
        metrics = (
            _planner_metrics(_mapping(row["metrics"], "metrics"))
            if isinstance(row.get("metrics"), Mapping)
            else {}
        )
        accepted = "promotion_candidate_id" in row
        evidence_bundle_id = (
            None if row.get("evidence_bundle_id") is None else str(row["evidence_bundle_id"])
        )
        lifecycle_status = _landscape_lifecycle_status(row, accepted=accepted)
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
            constraints=support._constraint_payload(run),
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


def _trial_evidence_rows(
    support: AutonomousResearchCampaignSupport,
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
        metrics = _metrics_from_trial_result(result)
        backtest = _mapping(metrics.get("backtest", {}), "backtest")
        quality = _mapping(metrics["quality"], "quality")
        trading = _mapping(metrics["trading"], "trading")
        rows.append(
            {
                "backtest_manifest_path": str(backtest.get("manifest_path", "")),
                "campaign_id": run.campaign_id,
                "candidate_id": str(trial["candidate_id"]),
                "candidate_space_hash": str(trial["candidate_space_hash"]),
                "evidence_bundle_id": result.evidence_bundle_id,
                "family": str(trial["family"]),
                "factor_family": str(trial["factor_family"]),
                "factor_hash": str(trial["factor_hash"]),
                "generation_id": generation_id,
                "manifest_hash": result.manifest_hash,
                "manifest_path": str(result.manifest_path),
                "metrics": dict(metrics),
                "metrics_path": str(result.metrics_path),
                "objective_value": quality["sharpe"],
                "parameters": dict(_mapping(trial["parameters"], "parameters")),
                "proposal_application": dict(
                    _mapping(
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


def _strategy_template(
    support: AutonomousResearchCampaignSupport,
    run: AutonomousResearchRun,
    family: ResearchCampaignFamily,
    search_space: SearchSpaceSpec,
) -> StrategyTemplate:
    path = support._config_path(family.manifest_template)
    if not path.exists():
        raise FileNotFoundError(f"strategy template config not found: {path}")
    payload = _yaml_mapping(path)
    factor_payload = payload.get("factor_definition")
    if not isinstance(factor_payload, Mapping):
        raise ValueError(f"strategy template factor_definition is required: {path}")
    factor_definition = support._factor_definition_for_family(
        run=run,
        family=family,
        template_payload=payload,
        static_factor_payload=cast(Mapping[str, Any], factor_payload),
        path=path,
    )
    manifest_template = dict(_mapping(payload.get("manifest_template", {}), "manifest"))
    backtest_pipeline = payload.get("backtest_pipeline")
    if backtest_pipeline is not None:
        manifest_template["backtest_pipeline"] = _mapping(
            backtest_pipeline,
            "backtest_pipeline",
        )
    return StrategyTemplate(
        template_id=str(payload.get("template_id", f"{family.template}_template")),
        family=family.id,
        factor_definition=factor_definition,
        strategy_entrypoint=str(
            payload.get("strategy_entrypoint", f"strategies.research.{family.id}:Strategy")
        ),
        allowed_imports=tuple(str(item) for item in payload.get("allowed_imports", ())),
        parameter_space=_parameter_space_payload(search_space),
        risk_assumptions=_mapping(
            payload.get("risk_assumptions", {"max_position_notional": 100000}),
            "risk_assumptions",
        ),
        execution_assumptions=_mapping(
            payload.get("execution_assumptions", {"slippage_bps": 1}),
            "execution_assumptions",
        ),
        manifest_template=manifest_template,
    )


def _budget_rejected_row(
    support: AutonomousResearchCampaignSupport,
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
        "parameters": dict(_mapping(trial["parameters"], "parameters")),
        "proposal_application": dict(
            _mapping(trial.get("proposal_application", {}), "proposal_application")
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


def _next_generation_proposal(
    support: AutonomousResearchCampaignSupport,
    *,
    run: AutonomousResearchRun,
    previous_generation_id: str,
    analytics: FitnessAnalytics,
    accepted_trial_count: int,
    data_window: Mapping[str, str],
) -> NextGenerationProposal:
    next_generation_number = int(previous_generation_id.rsplit("-", maxsplit=1)[1]) + 1
    remaining_trials = max(0, support._max_total_trials(run) - accepted_trial_count)
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


def _family_specs(
    support: AutonomousResearchCampaignSupport, run: AutonomousResearchRun
) -> tuple[Mapping[str, Any], ...]:
    if run.campaign_config is None:
        raise ValueError("autonomous research engine requires ResearchCampaignConfig")
    specs: list[Mapping[str, Any]] = []
    for family in run.campaign_config.families:
        search_space = support._search_space_from_path(family.search_space, run.universe)
        specs.append(
            {
                "family_id": family.id,
                "search_space": search_space,
                "template": _strategy_template(support, run, family, search_space),
            }
        )
    return tuple(specs)


__all__ = ["run"]
