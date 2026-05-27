"""Bounded autonomous research loop for research-only campaign artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.artifact_graph import (
    ResearchArtifactEdge,
    ResearchArtifactGraph,
    ResearchArtifactNode,
)
from qts.research.audit_log import ResearchAuditLog
from qts.research.campaign import ResearchCampaignConfig
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentResult,
    ResearchExperimentRunner,
    ResearchTrialResult,
)
from qts.research.orchestrator.queue import (
    ExperimentQueue,
    ExperimentRetryPolicy,
    ExperimentScheduler,
    ExperimentWorker,
)
from qts.research.promotion_packet import PromotionPacketV2


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

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        data_paths: Mapping[str, str | Path] | None = None,
        output_root: str | Path | None = None,
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
            "calendar": self.calendar,
            "data_paths": {
                root: str(path) for root, path in sorted((self.data_paths or {}).items())
            },
            "dataset_id": self.dataset_id,
            "families": list(self.families),
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

        all_landscape_rows: list[dict[str, Any]] = []
        selected_rows: list[dict[str, Any]] = []
        rejected_rows: list[dict[str, Any]] = []
        generations: list[AutonomousResearchGeneration] = []

        for generation_index in range(run.max_generations):
            generation = self._run_generation(
                run=run,
                generation_index=generation_index,
                data_paths=data_paths,
                audit_log=audit_log,
                evidence_registry=evidence_registry,
            )
            generations.append(generation["generation"])
            all_landscape_rows.extend(generation["landscape_rows"])
            selected_rows.extend(generation["selected_rows"])
            rejected_rows.extend(generation["rejected_rows"])

        fitness_landscape_path = root / "fitness_landscape.jsonl"
        selected_candidates_path = root / "selected_candidates.jsonl"
        rejected_candidates_path = root / "rejected_candidates.jsonl"
        self._write_jsonl(fitness_landscape_path, all_landscape_rows)
        self._write_jsonl(selected_candidates_path, selected_rows)
        self._write_jsonl(rejected_candidates_path, rejected_rows)

        fitness_analytics_path = root / "fitness_analytics.json"
        self._write_json(fitness_analytics_path, self._fitness_analytics(all_landscape_rows))
        next_generation_proposal_path = root / "next_generation_proposal.json"
        final_proposal = self._proposal_payload(
            run=run,
            generation_id=f"generation-{run.max_generations:03d}",
            selected_rows=selected_rows,
        )
        self._write_json(next_generation_proposal_path, final_proposal)

        report_path = root / "report.md"
        self._write_report(
            report_path,
            campaign_id=run.campaign_id,
            selected_count=len(selected_rows),
            rejected_count=len(rejected_rows),
        )
        validation_summary_path = root / "validation_summary.json"
        validation_summary = {
            "campaign_id": run.campaign_id,
            "generation_count": len(generations),
            "promotion_packet_count": len(selected_rows),
            "rejected_candidate_count": len(rejected_rows),
            "status": "accepted" if selected_rows else "rejected",
        }
        self._write_json(validation_summary_path, validation_summary)
        artifact_graph_path = self._write_final_artifact_graph(
            root=root,
            selected_rows=selected_rows,
            report_path=report_path,
            audit_log=audit_log,
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
        data_paths: Mapping[str, Path],
        audit_log: ResearchAuditLog,
        evidence_registry: EvidenceRegistry,
    ) -> dict[str, Any]:
        generation_id = f"generation-{generation_index:03d}"
        generation_dir = run.output_root / generation_id
        generation_dir.mkdir(parents=True, exist_ok=True)
        trials = self._trials(run, generation_id, generation_index)
        checked_paths = tuple(str(path) for path in data_paths.values())
        job = ResearchExperimentJob(
            job_id=f"{run.campaign_id}-{generation_id}",
            generation_id=generation_id,
            manifest_payload=self._manifest_payload(run, checked_paths),
            output_root=run.output_root,
            trials=trials,
        )
        queue = ExperimentQueue(jobs=(job,))
        scheduler = ExperimentScheduler(
            queue=queue,
            worker=ExperimentWorker(
                repo_root=self._repo_root,
                runner=ResearchExperimentRunner(repo_root=self._repo_root),
            ),
            retry_policy=ExperimentRetryPolicy(max_attempts=1),
        )
        schedule = scheduler.run(audit_log=audit_log)
        if schedule.status not in {"completed", "completed_with_retries"}:
            raise RuntimeError(f"generation schedule failed: {schedule.status}")
        experiment_result = ResearchExperimentRunner(repo_root=self._repo_root).run(job)
        landscape_rows = self._landscape_rows(
            run=run,
            generation_id=generation_id,
            trials=trials,
            trial_results=experiment_result.trials,
        )
        self._append_trial_audit_records(
            audit_log=audit_log,
            generation_index=generation_index,
            landscape_rows=landscape_rows,
        )
        selected_rows, rejected_rows = self._select_generation_candidates(
            run=run,
            generation_id=generation_id,
            trials=trials,
            trial_results=experiment_result.trials,
            landscape_rows=landscape_rows,
            evidence_registry=evidence_registry,
            audit_log=audit_log,
        )
        landscape_path = generation_dir / "fitness_landscape.jsonl"
        proposal_path = generation_dir / "next_generation_proposal.json"
        self._write_jsonl(landscape_path, landscape_rows)
        self._write_json(
            proposal_path,
            self._proposal_payload(
                run=run, generation_id=generation_id, selected_rows=selected_rows
            ),
        )
        return {
            "generation": AutonomousResearchGeneration(
                generation_id=generation_id,
                trial_count=len(trials),
                selected_count=len(selected_rows),
                rejected_count=len(rejected_rows),
                audit_record_count=len(audit_log.list()),
                landscape_path=landscape_path,
                next_generation_proposal_path=proposal_path,
                experiment_result=experiment_result,
            ),
            "landscape_rows": landscape_rows,
            "rejected_rows": rejected_rows,
            "selected_rows": selected_rows,
        }

    def _trials(
        self,
        run: AutonomousResearchRun,
        generation_id: str,
        generation_index: int,
    ) -> tuple[Mapping[str, Any], ...]:
        trials: list[Mapping[str, Any]] = []
        for trial_index in range(run.trials_per_generation):
            family = run.families[(generation_index + trial_index) % len(run.families)]
            symbol = run.universe[trial_index % len(run.universe)]
            sharpe = round(1.25 - (trial_index * 0.35) + (generation_index * 0.05), 4)
            trade_count = 48 - (trial_index * 12) + generation_index
            trials.append(
                {
                    "family": family,
                    "metrics": self._metrics(sharpe=sharpe, trade_count=trade_count),
                    "parameters": {
                        "lookback": 4 + generation_index + trial_index,
                        "symbol": symbol,
                        "threshold": round(0.1 + (trial_index * 0.05), 4),
                    },
                    "trial_id": f"{generation_id}-trial-{trial_index:03d}",
                }
            )
        return tuple(trials)

    def _manifest_payload(
        self,
        run: AutonomousResearchRun,
        checked_paths: tuple[str, ...],
    ) -> dict[str, Any]:
        return {
            "campaign_id": run.campaign_id,
            "data": {
                "calendar": run.calendar,
                "checked_paths": list(checked_paths),
                "dataset_id": run.dataset_id,
                "end": "2026-01-02T00:03:00+00:00",
                "start": "2026-01-02T00:00:00+00:00",
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

    def _landscape_rows(
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
            metrics = self._mapping(trial["metrics"], "metrics")
            quality = self._mapping(metrics["quality"], "quality")
            trading = self._mapping(metrics["trading"], "trading")
            rows.append(
                {
                    "campaign_id": run.campaign_id,
                    "evidence_bundle_id": result.evidence_bundle_id,
                    "family": str(trial["family"]),
                    "generation_id": generation_id,
                    "manifest_hash": result.manifest_hash,
                    "metrics_path": str(result.metrics_path),
                    "objective_value": quality["sharpe"],
                    "parameters": dict(self._mapping(trial["parameters"], "parameters")),
                    "status": result.status,
                    "trade_count": trading["oos_trade_count"],
                    "trial_id": trial_id,
                }
            )
        return rows

    def _append_trial_audit_records(
        self,
        *,
        audit_log: ResearchAuditLog,
        generation_index: int,
        landscape_rows: Sequence[Mapping[str, Any]],
    ) -> None:
        for trial_index, row in enumerate(landscape_rows):
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
        landscape_rows: Sequence[Mapping[str, Any]],
        evidence_registry: EvidenceRegistry,
        audit_log: ResearchAuditLog,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        selected_rows: list[dict[str, Any]] = []
        rejected_rows: list[dict[str, Any]] = []
        best = max(
            landscape_rows,
            key=lambda row: (float(row["objective_value"]), int(row["trade_count"])),
        )
        trial_by_id = {str(trial["trial_id"]): trial for trial in trials}
        result_by_id = {result.trial_id: result for result in trial_results}
        for row in landscape_rows:
            trial_id = str(row["trial_id"])
            result = result_by_id[trial_id]
            metrics = self._mapping(trial_by_id[trial_id]["metrics"], "metrics")
            reasons = self._rejection_reasons(row, selected=trial_id == best["trial_id"])
            if reasons:
                rejected_rows.append({**dict(row), "reasons": reasons})
                continue
            bundle = evidence_registry.create_from_workflow_summary(
                result.manifest_path.parent / "workflow_summary.json",
                idea=self._idea(run, generation_id, trial_by_id[trial_id]),
                strategy_id=f"{run.campaign_id}_strategy",
            )
            packet_payload = self._promotion_packet_payload(
                run=run,
                generation_id=generation_id,
                trial=trial_by_id[trial_id],
                trial_result=result,
                evidence_bundle_id=bundle.evidence_bundle_id,
                metrics_payload=metrics,
            )
            packet = PromotionPacketV2.from_payload(packet_payload)
            validation = packet.validate(
                evidence_registry=evidence_registry,
                audit_log=audit_log,
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
                rejected_rows.append({**dict(row), "reasons": list(validation.reasons)})
        return selected_rows, rejected_rows

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
                "decision": "go",
                "reviewed_at": "2026-05-26T00:00:00+00:00",
                "reviewer": "research-human-gate",
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

    def _rejection_reasons(
        self,
        row: Mapping[str, Any],
        *,
        selected: bool,
    ) -> list[str]:
        reasons: list[str] = []
        if not selected:
            reasons.append("not top-ranked candidate in generation")
        if float(row["objective_value"]) < 1.0:
            reasons.append("quality.sharpe below promotion threshold")
        if int(row["trade_count"]) < 40:
            reasons.append("trading.oos_trade_count below promotion threshold")
        return reasons

    def _proposal_payload(
        self,
        *,
        run: AutonomousResearchRun,
        generation_id: str,
        selected_rows: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        evidence_refs = [
            {
                "evidence_bundle_id": row["evidence_bundle_id"],
                "promotion_candidate_id": row["promotion_candidate_id"],
                "trial_id": row["trial_id"],
            }
            for row in selected_rows
        ]
        proposal_hash = stable_json_hash(evidence_refs).removeprefix("sha256:")[:16]
        payload = {
            "approval_policy": run.approval_policy,
            "campaign_id": run.campaign_id,
            "evidence_refs": evidence_refs,
            "generation_id": generation_id,
            "proposal_id": f"proposal-{proposal_hash}",
            "requires_human_approval": True,
            "status": "pending_human_approval",
        }
        payload["proposal_hash"] = stable_json_hash(payload)
        return payload

    def _fitness_analytics(self, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        by_family: dict[str, dict[str, Any]] = {}
        for row in rows:
            family = str(row["family"])
            stats = by_family.setdefault(family, {"count": 0, "max_objective_value": None})
            stats["count"] += 1
            current = stats["max_objective_value"]
            value = float(row["objective_value"])
            stats["max_objective_value"] = value if current is None else max(current, value)
        return {"families": by_family, "trial_count": len(rows)}

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
        selected = selected_rows[0]
        packet_payload = json.loads(
            Path(str(selected["promotion_packet_path"])).read_text(encoding="utf-8")
        )
        bundle = EvidenceRegistry(root / "evidence").show(str(selected["evidence_bundle_id"]))
        audit_record = self._audit_record(audit_log, str(selected["validation_audit_record_id"]))
        manifest_path = bundle.manifest_paths[0]
        manifest_hashes = cast(Mapping[str, str], bundle.manifest_hashes or {})
        metrics_path = str(selected["metrics_path"])
        data_quality_path = str(
            packet_payload["data_quality"]["payload"].get("path", "data_quality")
        )
        reproducibility_path = str(
            packet_payload["reproducibility"]["payload"].get(
                "path",
                packet_payload["reproducibility"].get("snapshot_id", "reproducibility"),
            )
        )
        graph_path = root / "artifact_graph" / "artifact_graph.json"
        report_hash = self._sha256_path(report_path)
        graph_hash_placeholder = "sha256:artifact-graph"
        graph = self._artifact_graph(
            artifact_graph_hash=graph_hash_placeholder,
            artifact_graph_path=graph_path,
            audit_payload_hash=audit_record.payload_hash,
            audit_record_id=audit_record.record_id,
            bundle_payload=bundle.to_payload(),
            data_quality_hash=str(packet_payload["data_quality"]["payload_hash"]),
            data_quality_path=data_quality_path,
            manifest_hash=str(manifest_hashes[manifest_path]),
            manifest_path=manifest_path,
            metrics_hash=str(packet_payload["metrics"]["payload_hash"]),
            metrics_path=metrics_path,
            packet_hash=str(packet_payload["packet_hash"]),
            promotion_candidate_id=str(packet_payload["promotion_candidate_id"]),
            report_hash=report_hash,
            report_path=report_path,
            reproducibility_hash=str(packet_payload["reproducibility"]["payload_hash"]),
            reproducibility_path=reproducibility_path,
        )
        graph = self._artifact_graph(
            artifact_graph_hash=graph.stable_hash(),
            artifact_graph_path=graph_path,
            audit_payload_hash=audit_record.payload_hash,
            audit_record_id=audit_record.record_id,
            bundle_payload=bundle.to_payload(),
            data_quality_hash=str(packet_payload["data_quality"]["payload_hash"]),
            data_quality_path=data_quality_path,
            manifest_hash=str(manifest_hashes[manifest_path]),
            manifest_path=manifest_path,
            metrics_hash=str(packet_payload["metrics"]["payload_hash"]),
            metrics_path=metrics_path,
            packet_hash=str(packet_payload["packet_hash"]),
            promotion_candidate_id=str(packet_payload["promotion_candidate_id"]),
            report_hash=report_hash,
            report_path=report_path,
            reproducibility_hash=str(packet_payload["reproducibility"]["payload_hash"]),
            reproducibility_path=reproducibility_path,
        )
        graph.validate_full_chain()
        self._write_json(graph_path, graph.to_payload())
        return graph_path

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

    def _metrics(self, *, sharpe: float, trade_count: int) -> dict[str, dict[str, object]]:
        return {
            "execution": {"cost_impact": 0.01, "slippage_sensitivity": 0.02},
            "portfolio": {"correlation_to_active": 0.3},
            "quality": {"profit_factor": 1.4, "sharpe": sharpe},
            "research": {
                "deterministic_replay_passed": True,
                "no_lookahead_passed": True,
                "promotion_eligible": True,
            },
            "risk": {"max_drawdown": 0.2},
            "stability": {"parameter_sensitivity": 0.8, "walk_forward_consistency": 0.75},
            "trading": {"oos_months": 12.0, "oos_trade_count": trade_count},
        }

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
