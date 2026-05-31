"""Stateless computation helpers for AutonomousResearchEngine.

Pure helper functions (artifact-graph / evidence projection, candidate-parameter rows,
audit records, strategy/backtest templates, manifest/promotion-packet payloads, and
small formatting/window utilities) extracted from AutonomousResearchEngine
(QTS-FINAL-011) as module functions threading their inputs (no engine state).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.data.historical.chains import HistoricalChain
from qts.registry.future_roll import (
    FirstNoticeDateFutureContractSelector,
    FutureContractCandidate,
    FutureContractRollSpec,
)
from qts.registry.providers.exchange_calendar_provider import ExchangeCalendarProvider
from qts.research.artifact_graph import (
    ResearchArtifactEdge,
    ResearchArtifactGraph,
    ResearchArtifactNode,
)
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.factory.strategy_template import StrategyTemplate
from qts.research.idea_spec import IdeaSpec
from qts.research.orchestrator.experiment_runner import (
    ResearchTrialResult,
)
from qts.research.planner import (
    NextGenerationProposal,
)
from qts.research.search import (
    SearchSpaceSpec,
)


def _active_correlation_context(
    *,
    candidate_id: str,
    trial_result: ResearchTrialResult,
) -> dict[str, Any]:
    metrics = json.loads(trial_result.metrics_path.read_text(encoding="utf-8"))
    backtest = _mapping(metrics.get("backtest", {}), "backtest")
    manifest_path = Path(str(backtest["manifest_path"]))
    return {
        "candidate_id": candidate_id,
        "manifest": json.loads(manifest_path.read_text(encoding="utf-8")),
        "manifest_path": str(manifest_path),
    }


def _active_correlation_context_from_selected(
    selected: Mapping[str, Any],
) -> dict[str, Any]:
    manifest_path = Path(str(selected["backtest_manifest_path"]))
    return {
        "candidate_id": str(selected["promotion_candidate_id"]),
        "manifest": json.loads(manifest_path.read_text(encoding="utf-8")),
        "manifest_path": str(manifest_path),
    }


def _append_trial_audit_records(
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


def _artifact_graph(
    *,
    artifact_graph_hash: str,
    artifact_graph_path: Path,
    audit_records: Sequence[Any],
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
    audit_nodes = tuple(
        ResearchArtifactNode(record.record_id, "audit_record", record.payload_hash)
        for record in audit_records
    )
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
        *audit_nodes,
        ResearchArtifactNode(str(report_path), "report", report_hash),
        ResearchArtifactNode(str(artifact_graph_path), "artifact_graph", artifact_graph_hash),
    )
    audit_edges = tuple(
        edge
        for record in audit_records
        for edge in (
            ResearchArtifactEdge(promotion_candidate_id, record.record_id, "references"),
            ResearchArtifactEdge(str(report_path), record.record_id, "references"),
        )
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
        ResearchArtifactEdge(str(report_path), promotion_candidate_id, "references"),
        ResearchArtifactEdge(str(report_path), str(artifact_graph_path), "references"),
        *audit_edges,
    )
    return ResearchArtifactGraph(nodes=nodes, edges=edges)


def _audit_records_for_selected(
    *,
    audit_log: ResearchAuditLog,
    selected: Mapping[str, Any],
    packet_payload: Mapping[str, Any],
) -> tuple[Any, ...]:
    evidence_bundle_id = str(selected["evidence_bundle_id"])
    promotion_candidate_id = str(packet_payload["promotion_candidate_id"])
    explicit_record_ids = {
        str(selected["validation_audit_record_id"]),
        str(packet_payload.get("audit_record_id", "")),
    }
    records = []
    for record in audit_log.list():
        payload = record.payload
        if (
            record.record_id in explicit_record_ids
            or payload.get("evidence_bundle_id") == evidence_bundle_id
            or payload.get("promotion_candidate_id") == promotion_candidate_id
        ):
            records.append(record)
    if not records:
        raise ValueError(f"audit records not found for {promotion_candidate_id}")
    return tuple(records)


def _backtest_pipeline_template(
    manifest_patch: Mapping[str, Any],
) -> dict[str, Any]:
    raw_template = manifest_patch.get("backtest_pipeline")
    if raw_template is None:
        return {}
    return dict(_mapping(raw_template, "backtest_pipeline"))


def _candidate_parameter_rows_from_trial_evidence(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "candidate_id": str(row["candidate_id"]),
            "candidate_space_hash": str(row["candidate_space_hash"]),
            "family": str(row["family"]),
            "generation_id": str(row["generation_id"]),
            "parameters": dict(_mapping(row["parameters"], "parameters")),
            "proposal_application": dict(
                _mapping(row.get("proposal_application", {}), "proposal_application")
            ),
            "strategy_variant_hash": str(row["strategy_variant_hash"]),
            "strategy_variant_id": str(row["strategy_variant_id"]),
            "trial_id": str(row["trial_id"]),
        }
        for row in rows
    )


def _candidate_parameter_rows_from_trials(
    trials: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "candidate_id": str(trial["candidate_id"]),
            "candidate_space_hash": str(trial["candidate_space_hash"]),
            "family": str(trial["family"]),
            "parameters": dict(_mapping(trial["parameters"], "parameters")),
            "proposal_application": dict(
                _mapping(trial.get("proposal_application", {}), "proposal_application")
            ),
            "strategy_variant_hash": str(trial["strategy_variant_hash"]),
            "strategy_variant_id": str(trial["strategy_variant_id"]),
            "trial_id": str(trial["trial_id"]),
        }
        for trial in trials
    )


def _default_materialized_contract_symbol(
    chain: HistoricalChain,
    *,
    as_of: datetime,
) -> str:
    return _materialized_contract_symbol_resolver(chain)(as_of)


def _default_strategy_parameter_bindings(
    root: str,
    parameters: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, str], None]:
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
    return strategy_parameter_defaults, strategy_parameter_map, None


def _edge_type(family: str) -> str:
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


def _ensure_full_backtest_csv(
    source_path: Path,
    target_path: Path,
    *,
    symbol: str,
    contract_symbol_for: Callable[[datetime], str] | None = None,
    window: tuple[str, str] | None,
    windows: Sequence[tuple[str, str]] = (),
) -> None:
    metadata_path = target_path.with_suffix(".materialization.json")
    source_stat = source_path.stat()
    expected_metadata = {
        "max_rows": None,
        "roll_aware_symbols": contract_symbol_for is not None,
        "source_path": str(source_path),
        "source_size": source_stat.st_size,
        "source_mtime_ns": source_stat.st_mtime_ns,
        "symbol": symbol,
        "window": None if window is None else {"end": window[1], "start": window[0]},
        "windows": [{"end": end, "start": start} for start, end in windows],
    }
    if target_path.exists() and metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata == expected_metadata:
            return
    temp_path = target_path.with_suffix(f"{target_path.suffix}.tmp")
    _materialize_backtest_csv(
        source_path,
        temp_path,
        symbol=symbol,
        contract_symbol_for=contract_symbol_for,
        max_rows=None,
        window=window,
        windows=windows,
    )
    temp_path.replace(target_path)
    _write_json(metadata_path, expected_metadata)


def _family_candidate_budget(
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


def _focused_family_order(proposal: NextGenerationProposal | None) -> tuple[str, ...]:
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


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _materialize_backtest_csv(
    source_path: Path,
    target_path: Path,
    *,
    symbol: str,
    contract_symbol_for: Callable[[datetime], str] | None = None,
    max_rows: int | None,
    window: tuple[str, str] | None = None,
    windows: Sequence[tuple[str, str]] = (),
) -> None:
    parsed_windows = _parsed_materialization_windows(window, windows)
    start_time = None if not parsed_windows else parsed_windows[0][0]
    end_time = None if not parsed_windows else parsed_windows[-1][1]
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
            symbol_index = header.index("symbol") if "symbol" in header else None
            for source_index, line in enumerate(source, start=1):
                if max_rows is not None and emitted >= max_rows:
                    break
                if not line.strip():
                    continue
                values = line.strip().split(",")
                timestamp = values[timestamp_index]
                timestamp_time = _parse_timestamp(timestamp)
                if start_time is not None and timestamp_time < start_time:
                    continue
                if end_time is not None and timestamp_time >= end_time:
                    break
                if parsed_windows and not _timestamp_in_windows(
                    timestamp_time,
                    parsed_windows,
                ):
                    continue
                if timestamp in seen_timestamps:
                    continue
                close = values[close_index]
                if close.startswith("-"):
                    continue
                output_symbol = (
                    values[symbol_index].strip()
                    if symbol_index is not None and values[symbol_index].strip()
                    else symbol
                )
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
                            output_symbol,
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
            timestamp_time = _parse_timestamp(timestamp)
            if start_time is not None and timestamp_time < start_time:
                continue
            if end_time is not None and timestamp_time >= end_time:
                break
            if parsed_windows and not _timestamp_in_windows(
                timestamp_time,
                parsed_windows,
            ):
                continue
            bar_symbol = (
                symbol if contract_symbol_for is None else contract_symbol_for(timestamp_time)
            )
            target.write(
                f"{timestamp},33,1,{index},{close},{close},{close},{close},1,{bar_symbol}\n"
            )
            emitted += 1
    if emitted == 0:
        raise ValueError(f"data path has no rows in requested backtest window: {source_path}")


def _materialized_contract_symbol_resolver(
    chain: HistoricalChain,
) -> Callable[[datetime], str]:
    """Return a roll-aware contract-symbol resolver keyed by bar timestamp.

    The continuous-future replay rolls between contracts using the chain's
    roll schedule, so a synthetic single-symbol fixture loses bars once a
    window crosses a roll boundary. Labelling each bar with the contract the
    roll selector considers active at that bar's session keeps every
    walk-forward window (train and out-of-sample) backed by real bars.
    """
    selector = FirstNoticeDateFutureContractSelector(
        contracts=tuple(
            FutureContractRollSpec(
                symbol=contract.symbol,
                instrument_id=chain.instrument_id_for_symbol(contract.symbol),
                first_notice_day=contract.first_notice_day,
                expiry=contract.expiry,
            )
            for contract in chain.contracts
        ),
        session_offset=ExchangeCalendarProvider(chain.trading_calendar).session_offset,
        active_months=chain.active_months,
    )
    cache: dict[date, str] = {}

    def resolve(as_of: datetime) -> str:
        session_date = as_of.date()
        cached = cache.get(session_date)
        if cached is not None:
            return cached
        candidates = tuple(
            FutureContractCandidate(
                root_symbol=chain.root,
                symbol=contract.symbol,
                instrument_id=chain.instrument_id_for_symbol(contract.symbol),
                as_of=as_of,
                close=Decimal("1"),
                volume=Decimal("1"),
                session_date=session_date,
            )
            for contract in chain.contracts
        )
        symbol = selector.select(candidates).symbol
        cache[session_date] = symbol
        return symbol

    return resolve


def _merged_selected_artifact_graph(
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
        audit_records = _audit_records_for_selected(
            audit_log=audit_log,
            selected=selected,
            packet_payload=packet_payload,
        )
        manifest_path = bundle.manifest_paths[0]
        manifest_hashes = cast(Mapping[str, str], bundle.manifest_hashes or {})
        graph = _artifact_graph(
            artifact_graph_hash=artifact_graph_hash,
            artifact_graph_path=artifact_graph_path,
            audit_records=audit_records,
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
                    packet_payload["reproducibility"].get("snapshot_id", "reproducibility"),
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
                and not _same_artifact_node(existing, node)
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


def _metrics_from_trial_result(result: ResearchTrialResult) -> Mapping[str, Any]:
    payload = json.loads(result.metrics_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"trial metrics artifact must be a JSON object: {result.metrics_path}")
    return dict(payload)


def _ordered_family_specs(
    family_specs: Sequence[Mapping[str, Any]],
    proposal: NextGenerationProposal | None,
) -> tuple[Mapping[str, Any], ...]:
    focus_order = _focused_family_order(proposal)
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


def _parameter_space_payload(search_space: SearchSpaceSpec) -> dict[str, Any]:
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


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace(".000000000Z", "+00:00").replace("Z", "+00:00"))


def _parsed_materialization_windows(
    window: tuple[str, str] | None,
    windows: Sequence[tuple[str, str]],
) -> tuple[tuple[datetime, datetime], ...]:
    raw_windows = tuple(windows) if windows else (() if window is None else (window,))
    return tuple((_parse_timestamp(start), _parse_timestamp(end)) for start, end in raw_windows)


def _planner_metrics(metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key not in {"backtest", "backtest_metrics", "backtest_statistics"}
    }


def _proposal_adjusted_template(
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


def _proposal_application_payload(
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


def _proposal_manifest_patch(
    manifest_patch: Mapping[str, Any],
    proposal: NextGenerationProposal | None,
) -> dict[str, Any]:
    patch = dict(manifest_patch)
    application = _proposal_application_payload(proposal)
    if not application:
        return patch
    research_factory = _mapping(patch.get("research_factory", {}), "research_factory")
    patch["research_factory"] = {
        **research_factory,
        "proposal_application": application,
    }
    return patch


def _round_robin_candidates(
    family_candidates: Sequence[tuple[Mapping[str, Any], tuple[Any, ...]]],
) -> tuple[tuple[Mapping[str, Any], Any], ...]:
    rows: list[tuple[Mapping[str, Any], Any]] = []
    max_length = max((len(candidates) for _, candidates in family_candidates), default=0)
    for index in range(max_length):
        for family, candidates in family_candidates:
            if index < len(candidates):
                rows.append((family, candidates[index]))
    return tuple(rows)


def _same_artifact_node(left: ResearchArtifactNode, right: ResearchArtifactNode) -> bool:
    return left.node_type == right.node_type and left.payload_hash == right.payload_hash


def _selector_candidate(
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
        "metrics": dict(_mapping(row["metrics"], "metrics")),
        "parameters": dict(_mapping(trial["parameters"], "parameters")),
        "reproducibility": json.loads(
            trial_result.reproducibility_path.read_text(encoding="utf-8")
        ),
        "validation": _validation_payload_from_artifacts(trial_result.validation_artifact_paths),
    }


def _sha256_path(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _strategy_parameter_bindings(
    *,
    root: str,
    parameters: Mapping[str, Any],
    pipeline_template: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, str] | None, tuple[str, ...] | None]:
    if not pipeline_template:
        return _default_strategy_parameter_bindings(root, parameters)

    raw_defaults = pipeline_template.get("strategy_parameter_defaults", {})
    defaults = _mapping(raw_defaults, "backtest_pipeline.strategy_parameter_defaults")
    strategy_parameter_defaults = dict(defaults)
    root_target = str(pipeline_template.get("root_strategy_parameter", "")).strip()
    if root_target == "symbols":
        strategy_parameter_defaults[root_target] = [root]
    elif root_target:
        strategy_parameter_defaults[root_target] = root

    raw_map = pipeline_template.get("strategy_parameter_map")
    raw_names = pipeline_template.get("strategy_parameter_names")
    if raw_map is not None and raw_names is not None:
        raise ValueError(
            "backtest_pipeline cannot define both strategy_parameter_map "
            "and strategy_parameter_names"
        )
    if raw_map is not None:
        parameter_map = _mapping(raw_map, "backtest_pipeline.strategy_parameter_map")
        return (
            strategy_parameter_defaults,
            {str(source): str(target) for source, target in parameter_map.items()},
            None,
        )
    if raw_names is None:
        raise ValueError(
            "backtest_pipeline requires strategy_parameter_names or strategy_parameter_map"
        )
    if not isinstance(raw_names, Sequence) or isinstance(raw_names, str):
        raise ValueError("backtest_pipeline.strategy_parameter_names must be a sequence")
    parameter_names = tuple(str(item) for item in raw_names)
    missing = [name for name in parameter_names if name not in parameters]
    if missing:
        raise ValueError(
            f"backtest_pipeline strategy parameter missing from trial parameters: {missing[0]}"
        )
    return strategy_parameter_defaults, None, parameter_names


def _template_idea_spec(
    template_payload: Mapping[str, Any],
    *,
    path: Path,
) -> IdeaSpec | None:
    discovery_payload = template_payload.get("factor_discovery")
    if discovery_payload is None:
        return None
    discovery = _mapping(discovery_payload, "factor_discovery")
    idea_payload = discovery.get("idea_spec")
    if not isinstance(idea_payload, Mapping):
        raise ValueError(f"strategy template factor_discovery.idea_spec is required: {path}")
    return IdeaSpec.from_payload(cast(Mapping[str, Any], idea_payload))


def _timestamp_in_windows(
    timestamp: datetime,
    windows: Sequence[tuple[datetime, datetime]],
) -> bool:
    return any(start <= timestamp < end for start, end in windows)


def _validation_payload_from_artifacts(
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


def _write_empty_artifact_graph(root: Path) -> Path:
    graph_path = root / "artifact_graph" / "artifact_graph.json"
    _write_json(graph_path, ResearchArtifactGraph().to_payload())
    return graph_path


def _write_final_artifact_graph(
    *,
    root: Path,
    selected_rows: Sequence[Mapping[str, Any]],
    report_path: Path,
    audit_log: ResearchAuditLog,
) -> Path:
    if not selected_rows:
        raise ValueError("artifact graph requires at least one selected candidate")
    graph_path = root / "artifact_graph" / "artifact_graph.json"
    report_hash = _sha256_path(report_path)
    graph = _merged_selected_artifact_graph(
        artifact_graph_hash="sha256:artifact-graph",
        artifact_graph_path=graph_path,
        audit_log=audit_log,
        report_hash=report_hash,
        report_path=report_path,
        root=root,
        selected_rows=selected_rows,
    )
    graph = _merged_selected_artifact_graph(
        artifact_graph_hash=graph.stable_hash(),
        artifact_graph_path=graph_path,
        audit_log=audit_log,
        report_hash=report_hash,
        report_path=report_path,
        root=root,
        selected_rows=selected_rows,
    )
    graph.validate_full_chain()
    _write_json(graph_path, graph.to_payload())
    return graph_path


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(dict(row), sort_keys=True) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _write_next_generation_proposal(
    path: Path,
    proposal: NextGenerationProposal,
) -> None:
    payload = proposal.to_payload()
    evidence_refs = sorted(
        {ref for mutation in proposal.mutations for ref in mutation.evidence_refs if ref.strip()}
    )
    _write_json(
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


def _write_report(
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


def _yaml_mapping(path: Path) -> Mapping[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError(f"YAML config must be a mapping: {path}")
    return dict(raw)


__all__ = [
    "_active_correlation_context",
    "_active_correlation_context_from_selected",
    "_append_trial_audit_records",
    "_artifact_graph",
    "_audit_records_for_selected",
    "_backtest_pipeline_template",
    "_candidate_parameter_rows_from_trial_evidence",
    "_candidate_parameter_rows_from_trials",
    "_default_materialized_contract_symbol",
    "_default_strategy_parameter_bindings",
    "_edge_type",
    "_ensure_full_backtest_csv",
    "_family_candidate_budget",
    "_focused_family_order",
    "_landscape_lifecycle_status",
    "_mapping",
    "_materialize_backtest_csv",
    "_materialized_contract_symbol_resolver",
    "_merged_selected_artifact_graph",
    "_metrics_from_trial_result",
    "_ordered_family_specs",
    "_parameter_space_payload",
    "_parse_timestamp",
    "_parsed_materialization_windows",
    "_planner_metrics",
    "_proposal_adjusted_template",
    "_proposal_application_payload",
    "_proposal_manifest_patch",
    "_round_robin_candidates",
    "_same_artifact_node",
    "_selector_candidate",
    "_sha256_path",
    "_strategy_parameter_bindings",
    "_template_idea_spec",
    "_timestamp_in_windows",
    "_validation_payload_from_artifacts",
    "_write_empty_artifact_graph",
    "_write_final_artifact_graph",
    "_write_json",
    "_write_jsonl",
    "_write_next_generation_proposal",
    "_write_report",
    "_yaml_mapping",
]
