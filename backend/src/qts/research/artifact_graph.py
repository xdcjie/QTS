"""Deterministic research artifact relationship graph."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.audit_log import ResearchAuditLog


@dataclass(frozen=True, slots=True)
class ResearchArtifactNode:
    """One artifact object in a research evidence graph."""

    node_id: str
    node_type: str
    payload_hash: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id is required")
        if self.node_type not in _NODE_TYPES:
            raise ValueError(f"unsupported node_type: {self.node_type}")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchArtifactNode:
        """Rehydrate a node from a JSON payload."""

        metadata = payload.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("node metadata must be a mapping")
        payload_hash = payload.get("payload_hash")
        return cls(
            node_id=cls._required_text(payload, "node_id"),
            node_type=cls._required_text(payload, "node_type"),
            payload_hash=None if payload_hash is None else str(payload_hash),
            metadata=dict(metadata),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready node payload."""

        return {
            "metadata": dict(self.metadata),
            "node_id": self.node_id,
            "node_type": self.node_type,
            "payload_hash": self.payload_hash,
        }

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()


@dataclass(frozen=True, slots=True)
class ResearchArtifactEdge:
    """A typed relationship between two artifact graph nodes."""

    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")
        if not self.target_id.strip():
            raise ValueError("target_id is required")
        if not self.relation.strip():
            raise ValueError("relation is required")

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchArtifactEdge:
        """Rehydrate an edge from a JSON payload."""

        return cls(
            source_id=ResearchArtifactNode._required_text(payload, "source_id"),
            target_id=ResearchArtifactNode._required_text(payload, "target_id"),
            relation=ResearchArtifactNode._required_text(payload, "relation"),
        )

    def to_payload(self) -> dict[str, str]:
        """Return a deterministic JSON-ready edge payload."""

        return {
            "relation": self.relation,
            "source_id": self.source_id,
            "target_id": self.target_id,
        }


@dataclass(frozen=True, slots=True)
class ResearchArtifactGraph:
    """Deterministic DAG of research artifact object relationships."""

    nodes: tuple[ResearchArtifactNode, ...] = ()
    edges: tuple[ResearchArtifactEdge, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nodes",
            tuple(
                sorted(
                    self.nodes,
                    key=lambda node: (node.node_id, node.node_type, node.payload_hash or ""),
                )
            ),
        )
        object.__setattr__(
            self,
            "edges",
            tuple(
                sorted(
                    self.edges,
                    key=lambda edge: (edge.source_id, edge.target_id, edge.relation),
                )
            ),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchArtifactGraph:
        """Rehydrate a graph from a JSON payload."""

        nodes = cls._sequence(payload.get("nodes", ()), "nodes")
        edges = cls._sequence(payload.get("edges", ()), "edges")
        return cls(
            nodes=tuple(ResearchArtifactNode.from_payload(node) for node in nodes),
            edges=tuple(ResearchArtifactEdge.from_payload(edge) for edge in edges),
        )

    def validate(self) -> None:
        """Validate graph references, acyclicity, and present-node artifact links."""

        nodes_by_id = self._nodes_by_id()
        for edge in self.edges:
            if edge.source_id not in nodes_by_id:
                raise ValueError(f"edge source_id is not a node: {edge.source_id}")
            if edge.target_id not in nodes_by_id:
                raise ValueError(f"edge target_id is not a node: {edge.target_id}")
        self._validate_required_edges(nodes_by_id)
        self._validate_acyclic(nodes_by_id)

    def validate_full_chain(self) -> None:
        """Validate the complete Research OS v1.0 promotion evidence graph."""

        self.validate()
        self._validate_payload_hashes()
        self._validate_required_node_types()

    def stable_hash(self) -> str:
        """Return the order-independent hash for this graph's evidence relationships."""

        return stable_json_hash(self._stable_payload())

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready graph payload."""

        return {
            "edges": [edge.to_payload() for edge in self.edges],
            "nodes": [node.to_payload() for node in self.nodes],
        }

    def _stable_payload(self) -> dict[str, Any]:
        return {
            "edges": [edge.to_payload() for edge in self.edges],
            "nodes": [self._stable_node_payload(node) for node in self.nodes],
        }

    def _stable_node_payload(self, node: ResearchArtifactNode) -> dict[str, Any]:
        payload = node.to_payload()
        if node.node_type in _SELF_REFERENTIAL_NODE_TYPES:
            payload["payload_hash"] = f"self-referential:{node.node_type}"
        return payload

    @staticmethod
    def _sequence(value: Any, field_name: str) -> Sequence[Mapping[str, Any]]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise ValueError(f"{field_name} must be a sequence")
        for item in value:
            if not isinstance(item, Mapping):
                raise ValueError(f"{field_name} must contain mappings")
        return value

    def _nodes_by_id(self) -> dict[str, ResearchArtifactNode]:
        nodes_by_id: dict[str, ResearchArtifactNode] = {}
        for node in self.nodes:
            if node.node_id in nodes_by_id:
                raise ValueError(f"duplicate node_id: {node.node_id}")
            nodes_by_id[node.node_id] = node
        return nodes_by_id

    def _validate_required_node_types(self) -> None:
        node_types = {node.node_type for node in self.nodes}
        for node_type in sorted(_REQUIRED_NODE_TYPES):
            if node_type not in node_types:
                raise ValueError(f"artifact graph missing required node_type: {node_type}")

    def _validate_payload_hashes(self) -> None:
        for node in self.nodes:
            if not node.payload_hash:
                raise ValueError(
                    f"artifact graph node missing payload_hash: {node.node_type}:{node.node_id}"
                )

    def _validate_required_edges(self, nodes_by_id: Mapping[str, ResearchArtifactNode]) -> None:
        node_types = {node.node_type for node in self.nodes}
        for source_type, target_type, message in _REQUIRED_REFERENCES:
            if target_type not in node_types:
                continue
            for source in self.nodes:
                if source.node_type != source_type:
                    continue
                if not self._has_reference_to_type(source.node_id, target_type, nodes_by_id):
                    raise ValueError(message)

    def _has_reference_to_type(
        self,
        source_id: str,
        target_type: str,
        nodes_by_id: Mapping[str, ResearchArtifactNode],
    ) -> bool:
        return any(
            edge.source_id == source_id
            and edge.relation == "references"
            and nodes_by_id[edge.target_id].node_type == target_type
            for edge in self.edges
        )

    def _validate_acyclic(self, nodes_by_id: Mapping[str, ResearchArtifactNode]) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()
        adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes_by_id}
        for edge in self.edges:
            adjacency[edge.source_id].append(edge.target_id)

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                raise ValueError(f"artifact graph contains a cycle at node: {node_id}")
            visiting.add(node_id)
            for target_id in adjacency[node_id]:
                visit(target_id)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in nodes_by_id:
            visit(node_id)


class ResearchArtifactGraphBuilder:
    """Owns construction of research artifact graphs from artifact payloads."""

    def build(
        self,
        *,
        manifests: Sequence[Mapping[str, Any]] = (),
        workflow_runs: Sequence[Mapping[str, Any]] = (),
        evidence_bundles: Sequence[Mapping[str, Any]] = (),
        metrics: Sequence[Mapping[str, Any]] = (),
        data_quality_artifacts: Sequence[Mapping[str, Any]] = (),
        reproducibility_snapshots: Sequence[Mapping[str, Any]] = (),
        promotion_packets: Sequence[Mapping[str, Any]] = (),
        audit_records: Sequence[Mapping[str, Any]] = (),
        reports: Sequence[Mapping[str, Any]] = (),
        artifact_graphs: Sequence[Mapping[str, Any]] = (),
    ) -> ResearchArtifactGraph:
        """Build and validate a deterministic artifact relationship graph."""

        nodes_by_id: dict[str, ResearchArtifactNode] = {}
        edges: list[ResearchArtifactEdge] = []
        manifest_hashes: dict[str, str] = {}

        for manifest in manifests:
            node = self._node(manifest, "manifest", self._manifest_id)
            self._add_node(nodes_by_id, node)
            if node.payload_hash is not None:
                manifest_hashes[node.node_id] = node.payload_hash

        for workflow_run in workflow_runs:
            workflow_node = self._node(workflow_run, "workflow_run", self._workflow_run_id)
            self._add_node(nodes_by_id, workflow_node)
            for manifest_ref in self._manifest_refs(workflow_run):
                manifest_node = self._manifest_node_from_ref(manifest_ref, manifest_hashes)
                self._add_node(nodes_by_id, manifest_node)
                self._add_edge(edges, workflow_node.node_id, manifest_node.node_id)

        for evidence_bundle in evidence_bundles:
            evidence_node = self._node(
                evidence_bundle,
                "evidence_bundle",
                self._evidence_bundle_id,
            )
            self._add_node(nodes_by_id, evidence_node)
            bundle_manifest_hashes = self._string_mapping(
                evidence_bundle.get("manifest_hashes", {})
            )
            for manifest_ref in self._manifest_refs(evidence_bundle):
                known_manifest_hashes = {**manifest_hashes, **bundle_manifest_hashes}
                manifest_node = self._manifest_node_from_ref(
                    manifest_ref,
                    known_manifest_hashes,
                )
                self._add_node(nodes_by_id, manifest_node)
                edges.append(
                    ResearchArtifactEdge(
                        source_id=evidence_node.node_id,
                        target_id=manifest_node.node_id,
                        relation="references",
                    )
                )

        for metric in metrics:
            self._add_node(nodes_by_id, self._node(metric, "metrics", self._metrics_id))

        for data_quality in data_quality_artifacts:
            self._add_node(
                nodes_by_id,
                self._node(data_quality, "data_quality", self._data_quality_id),
            )

        for reproducibility in reproducibility_snapshots:
            self._add_node(
                nodes_by_id,
                self._node(reproducibility, "reproducibility", self._reproducibility_id),
            )

        section_refs_by_evidence_bundle: dict[str, list[str]] = {}
        for promotion_packet in promotion_packets:
            packet_node = self._node(
                promotion_packet,
                "promotion_packet",
                self._promotion_packet_id,
            )
            self._add_node(nodes_by_id, packet_node)
            evidence_bundle_id = self._required_text(promotion_packet, "evidence_bundle_id")
            self._add_edge(edges, packet_node.node_id, evidence_bundle_id)
            for section_name, node_type, resolver in _PACKET_SECTION_TYPES:
                section_node = self._section_node(
                    promotion_packet,
                    section_name,
                    node_type,
                    resolver,
                    packet_node.node_id,
                )
                self._add_node(nodes_by_id, section_node)
                self._add_edge(edges, packet_node.node_id, section_node.node_id)
                section_refs_by_evidence_bundle.setdefault(evidence_bundle_id, []).append(
                    section_node.node_id
                )
            self._add_edge(
                edges,
                packet_node.node_id,
                self._required_text(promotion_packet, "audit_record_id"),
            )

        for evidence_bundle_id, section_node_ids in section_refs_by_evidence_bundle.items():
            for section_node_id in section_node_ids:
                self._add_edge(edges, evidence_bundle_id, section_node_id)

        for audit_record in audit_records:
            self._add_node(
                nodes_by_id,
                self._node(audit_record, "audit_record", self._audit_record_id),
            )

        for artifact_graph in artifact_graphs:
            self._add_node(
                nodes_by_id,
                self._node(artifact_graph, "artifact_graph", self._artifact_graph_id),
            )

        for report in reports:
            report_node = self._node(report, "report", self._report_id)
            report_refs = self._report_refs(report)
            self._add_node(nodes_by_id, report_node)
            self._add_edge(
                edges,
                report_node.node_id,
                self._required_text(report_refs, "promotion_packet_id"),
            )
            self._add_edge(
                edges,
                report_node.node_id,
                self._required_text(report_refs, "audit_record_id"),
            )
            artifact_graph_node = self._artifact_graph_node_from_ref(report_refs)
            self._add_node(nodes_by_id, artifact_graph_node)
            self._add_edge(edges, report_node.node_id, artifact_graph_node.node_id)

        graph = ResearchArtifactGraph(nodes=tuple(nodes_by_id.values()), edges=tuple(edges))
        graph.validate()
        return graph

    def _add_node(
        self,
        nodes_by_id: dict[str, ResearchArtifactNode],
        node: ResearchArtifactNode,
    ) -> None:
        existing = nodes_by_id.get(node.node_id)
        if existing is None:
            nodes_by_id[node.node_id] = node
            return
        if existing.node_type != node.node_type:
            raise ValueError(f"node_id has conflicting node_type: {node.node_id}")
        if existing.payload_hash is not None and node.payload_hash is not None:
            if existing.payload_hash != node.payload_hash:
                raise ValueError(f"node_id has conflicting payload_hash: {node.node_id}")
            return
        if existing.payload_hash is None and node.payload_hash is not None:
            nodes_by_id[node.node_id] = node

    def _add_edge(
        self,
        edges: list[ResearchArtifactEdge],
        source_id: str,
        target_id: str,
    ) -> None:
        edge = ResearchArtifactEdge(
            source_id=source_id,
            target_id=target_id,
            relation="references",
        )
        if edge not in edges:
            edges.append(edge)

    def _node(
        self,
        payload: Mapping[str, Any],
        node_type: str,
        node_id_resolver: Any,
    ) -> ResearchArtifactNode:
        return ResearchArtifactNode(
            node_id=node_id_resolver(payload),
            node_type=node_type,
            payload_hash=self._payload_hash(payload),
            metadata=self._metadata(payload),
        )

    def _section_node(
        self,
        payload: Mapping[str, Any],
        section_name: str,
        node_type: str,
        node_id_resolver: Any,
        packet_id: str,
    ) -> ResearchArtifactNode:
        section = payload.get(section_name)
        if not isinstance(section, Mapping):
            raise ValueError(f"promotion_packet {section_name} section is required")
        node_id = self._optional_first_text(section, _SECTION_ID_FIELDS[section_name])
        return ResearchArtifactNode(
            node_id=node_id or f"{packet_id}:{section_name}",
            node_type=node_type,
            payload_hash=self._payload_hash(section),
            metadata={
                **dict(self._metadata(section)),
                "packet_section": section_name,
            },
        )

    def _manifest_node_from_ref(
        self,
        manifest_ref: str | Mapping[str, Any],
        manifest_hashes: Mapping[str, str],
    ) -> ResearchArtifactNode:
        if isinstance(manifest_ref, Mapping):
            return self._node(manifest_ref, "manifest", self._manifest_id)
        manifest_id = manifest_ref.strip()
        if not manifest_id:
            raise ValueError("manifest reference is required")
        return ResearchArtifactNode(
            node_id=manifest_id,
            node_type="manifest",
            payload_hash=manifest_hashes.get(manifest_id),
            metadata={},
        )

    def _manifest_refs(self, payload: Mapping[str, Any]) -> tuple[str | Mapping[str, Any], ...]:
        for field_name in ("manifest_refs", "manifests"):
            value = payload.get(field_name)
            if value is not None:
                return self._ref_tuple(value, field_name)
        for field_name in ("manifest_ids", "manifest_paths"):
            value = payload.get(field_name)
            if value is not None:
                return tuple(str(item).strip() for item in self._sequence(value, field_name))
        for field_name in ("manifest_id", "manifest_path"):
            value = payload.get(field_name)
            if value is not None:
                return (self._text(value, field_name),)
        manifest_hashes = self._string_mapping(payload.get("manifest_hashes", {}))
        if manifest_hashes:
            return tuple(sorted(manifest_hashes))
        raise ValueError("evidence_bundle must reference at least one manifest")

    def _artifact_graph_node_from_ref(
        self,
        payload: Mapping[str, Any],
    ) -> ResearchArtifactNode:
        artifact_graph_hash = payload.get("artifact_graph_hash")
        for field_name in ("artifact_graph_id", "artifact_graph_path", "path"):
            value = payload.get(field_name)
            if value is not None:
                if artifact_graph_hash is None:
                    raise ValueError("artifact_graph_hash is required")
                return ResearchArtifactNode(
                    node_id=self._text(value, field_name),
                    node_type="artifact_graph",
                    payload_hash=self._text(artifact_graph_hash, "artifact_graph_hash"),
                    metadata={},
                )
        if artifact_graph_hash is None:
            raise ValueError("artifact_graph_id is required")
        graph_hash = self._text(artifact_graph_hash, "artifact_graph_hash")
        return ResearchArtifactNode(
            node_id=graph_hash,
            node_type="artifact_graph",
            payload_hash=graph_hash,
            metadata={},
        )

    def _report_refs(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        projection_refs = payload.get("projection_refs")
        if projection_refs is None:
            return payload
        if not isinstance(projection_refs, Mapping):
            raise ValueError("projection_refs must be a mapping")
        return projection_refs

    def _metadata(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        return {str(key): self._json_safe(value) for key, value in metadata.items()}

    def _payload_hash(self, payload: Mapping[str, Any]) -> str:
        value = payload.get("payload_hash")
        if value is not None:
            return self._text(value, "payload_hash")
        for field_name in ("artifact_hash", "manifest_hash", "packet_hash", "report_hash"):
            value = payload.get(field_name)
            if value is not None:
                return self._text(value, field_name)
        return stable_json_hash(self._json_safe(payload))

    def _manifest_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("manifest_id", "node_id", "path", "manifest_path"))

    def _workflow_run_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("workflow_run_id", "run_id", "node_id", "path"))

    def _evidence_bundle_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("evidence_bundle_id", "node_id"))

    def _metrics_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, _SECTION_ID_FIELDS["metrics"])

    def _data_quality_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, _SECTION_ID_FIELDS["data_quality"])

    def _reproducibility_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, _SECTION_ID_FIELDS["reproducibility"])

    def _promotion_packet_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(
            payload,
            ("promotion_packet_id", "packet_id", "promotion_candidate_id", "node_id"),
        )

    def _audit_record_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("record_id", "audit_record_id", "node_id"))

    def _report_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("report_id", "workflow_id", "node_id", "path"))

    def _artifact_graph_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(
            payload,
            ("artifact_graph_id", "node_id", "path", "artifact_graph_path", "artifact_graph_hash"),
        )

    def _first_text(self, payload: Mapping[str, Any], field_names: Sequence[str]) -> str:
        for field_name in field_names:
            value = payload.get(field_name)
            if value is not None:
                return self._text(value, field_name)
        raise ValueError(f"{field_names[0]} is required")

    def _optional_first_text(
        self,
        payload: Mapping[str, Any],
        field_names: Sequence[str],
    ) -> str | None:
        for field_name in field_names:
            value = payload.get(field_name)
            if value is not None:
                return self._text(value, field_name)
        return None

    def _required_text(self, payload: Mapping[str, Any], field_name: str) -> str:
        if field_name == "promotion_packet_id":
            return self._first_text(payload, ("promotion_packet_id", "packet_id"))
        if field_name == "audit_record_id":
            return self._first_text(
                payload,
                ("audit_record_id", "human_review_record_id", "record_id"),
            )
        return self._text(payload.get(field_name), field_name)

    def _text(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    def _ref_tuple(self, value: Any, field_name: str) -> tuple[str | Mapping[str, Any], ...]:
        refs = self._sequence(value, field_name)
        normalized: list[str | Mapping[str, Any]] = []
        for item in refs:
            if isinstance(item, Mapping):
                normalized.append(item)
            else:
                normalized.append(self._text(item, field_name))
        return tuple(normalized)

    def _sequence(self, value: Any, field_name: str) -> Sequence[Any]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise ValueError(f"{field_name} must be a sequence")
        return value

    def _string_mapping(self, value: Any) -> Mapping[str, str]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("expected string mapping")
        return {str(key): str(item) for key, item in value.items()}

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, Mapping):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, str):
            return [self._json_safe(item) for item in value]
        return value


class ResearchArtifactGraphWriter:
    """Owns deterministic persistence of research artifact graphs."""

    @dataclass(frozen=True, slots=True)
    class WriteResult:
        """Result returned after persisting an artifact graph."""

        path: Path
        artifact_graph_hash: str
        graph: ResearchArtifactGraph

    def __init__(self, output_root: str | Path) -> None:
        self._output_root = Path(output_root)

    def write(
        self,
        graph: ResearchArtifactGraph,
        *,
        output_path: str | Path = "artifact-graph.json",
        audit_log: ResearchAuditLog | None = None,
    ) -> WriteResult:
        """Validate and write a deterministic JSON artifact graph payload."""

        if audit_log is None:
            raise ValueError("artifact graph writes require ResearchAuditLog")
        graph.validate()
        target = self._resolve_output_path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(stable_json_dumps(graph.to_payload()) + "\n", encoding="utf-8")
        result = self.WriteResult(
            path=target,
            artifact_graph_hash=graph.stable_hash(),
            graph=graph,
        )
        self._append_written_record(audit_log, result)
        return result

    def write_from_payloads(
        self,
        *,
        manifests: Sequence[Mapping[str, Any]] = (),
        workflow_runs: Sequence[Mapping[str, Any]] = (),
        evidence_bundles: Sequence[Mapping[str, Any]] = (),
        metrics: Sequence[Mapping[str, Any]] = (),
        data_quality_artifacts: Sequence[Mapping[str, Any]] = (),
        reproducibility_snapshots: Sequence[Mapping[str, Any]] = (),
        promotion_packets: Sequence[Mapping[str, Any]] = (),
        audit_records: Sequence[Mapping[str, Any]] = (),
        reports: Sequence[Mapping[str, Any]] = (),
        artifact_graphs: Sequence[Mapping[str, Any]] = (),
        output_path: str | Path = "artifact-graph.json",
        audit_log: ResearchAuditLog | None = None,
    ) -> WriteResult:
        """Build, validate, and persist a graph from artifact payloads."""

        graph = ResearchArtifactGraphBuilder().build(
            manifests=manifests,
            workflow_runs=workflow_runs,
            evidence_bundles=evidence_bundles,
            metrics=metrics,
            data_quality_artifacts=data_quality_artifacts,
            reproducibility_snapshots=reproducibility_snapshots,
            promotion_packets=promotion_packets,
            audit_records=audit_records,
            reports=reports,
            artifact_graphs=artifact_graphs,
        )
        return self.write(graph, output_path=output_path, audit_log=audit_log)

    def write_dry_run_artifacts(
        self,
        *,
        artifact_dir: Path,
        manifest_path: Path,
        resolved_manifest: Mapping[str, Any],
        metrics_payload: Mapping[str, Any],
        data_quality_payload: Mapping[str, Any],
        reproducibility_payload: Mapping[str, Any],
        output_path: str | Path = "artifact_graph.json",
        audit_log: ResearchAuditLog | None = None,
    ) -> WriteResult:
        """Write the graph linking dry-run evidence artifacts to the manifest."""

        manifest_node_id = str(manifest_path)
        artifact_nodes = (
            ResearchArtifactNode(
                node_id=manifest_node_id,
                node_type="manifest",
                payload_hash=stable_json_hash(resolved_manifest),
            ),
            ResearchArtifactNode(
                node_id=str(artifact_dir / "metrics.json"),
                node_type="metrics",
                payload_hash=stable_json_hash(metrics_payload),
            ),
            ResearchArtifactNode(
                node_id=str(artifact_dir / "data_quality.json"),
                node_type="data_quality",
                payload_hash=str(data_quality_payload.get("artifact_hash", "")) or None,
            ),
            ResearchArtifactNode(
                node_id=str(artifact_dir / "reproducibility_v2.json"),
                node_type="reproducibility",
                payload_hash=stable_json_hash(reproducibility_payload),
            ),
        )
        graph = ResearchArtifactGraph(
            nodes=artifact_nodes,
            edges=tuple(
                ResearchArtifactEdge(
                    source_id=node.node_id,
                    target_id=manifest_node_id,
                    relation="references",
                )
                for node in artifact_nodes
                if node.node_id != manifest_node_id
            ),
        )
        return self.write(graph, output_path=output_path, audit_log=audit_log)

    def _append_written_record(
        self,
        audit_log: ResearchAuditLog,
        result: WriteResult,
    ) -> None:
        audit_log.append(
            "artifact_graph_written",
            {
                "artifact_graph_hash": result.artifact_graph_hash,
                "artifact_graph_path": str(result.path),
                "edge_count": len(result.graph.edges),
                "node_count": len(result.graph.nodes),
            },
        )

    def _resolve_output_path(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        if path.is_absolute():
            raise ValueError("output_path must be relative to artifact graph output root")
        if any(part == ".." for part in path.parts):
            raise ValueError("output_path must not use parent traversal")
        if path.as_posix() in {"", "."}:
            raise ValueError("output_path must include a filename")

        root = self._output_root.resolve()
        target = (root / path).resolve()
        if not target.is_relative_to(root):
            raise ValueError("output_path must remain inside artifact graph output root")
        return target


_NODE_TYPES = frozenset(
    {
        "idea",
        "campaign",
        "factor_definition",
        "strategy_variant",
        "search_space",
        "trial_budget",
        "candidate_result",
        "selection_result",
        "validation_result",
        "fitness_landscape",
        "fitness_analytics",
        "next_generation_proposal",
        "generation_approval",
        "manifest",
        "workflow_run",
        "experiment_manifest",
        "metrics",
        "data_quality",
        "reproducibility",
        "evidence_bundle",
        "promotion_packet",
        "audit_record",
        "report",
        "artifact_graph",
    }
)

_REQUIRED_NODE_TYPES = frozenset(
    {
        "manifest",
        "workflow_run",
        "evidence_bundle",
        "metrics",
        "data_quality",
        "reproducibility",
        "promotion_packet",
        "audit_record",
        "report",
        "artifact_graph",
    }
)

_SELF_REFERENTIAL_NODE_TYPES = frozenset({"artifact_graph", "evidence_bundle", "report"})

_REQUIRED_REFERENCES = (
    ("workflow_run", "manifest", "workflow_run must reference manifest"),
    ("evidence_bundle", "manifest", "evidence_bundle must reference manifest"),
    ("evidence_bundle", "metrics", "evidence_bundle must reference metrics"),
    ("evidence_bundle", "data_quality", "evidence_bundle must reference data_quality"),
    (
        "evidence_bundle",
        "reproducibility",
        "evidence_bundle must reference reproducibility",
    ),
    (
        "promotion_packet",
        "evidence_bundle",
        "promotion_packet must reference evidence_bundle",
    ),
    ("promotion_packet", "metrics", "promotion_packet must reference metrics"),
    ("promotion_packet", "data_quality", "promotion_packet must reference data_quality"),
    (
        "promotion_packet",
        "reproducibility",
        "promotion_packet must reference reproducibility",
    ),
    ("promotion_packet", "audit_record", "promotion_packet must reference audit_record"),
    ("report", "promotion_packet", "report must reference promotion_packet"),
    ("report", "audit_record", "report must reference audit_record"),
    ("report", "artifact_graph", "report must reference artifact_graph"),
)

_SECTION_ID_FIELDS = {
    "metrics": ("metrics_id", "artifact_id", "node_id", "path", "metrics_path"),
    "data_quality": (
        "data_quality_id",
        "artifact_id",
        "node_id",
        "path",
        "data_quality_path",
    ),
    "reproducibility": (
        "reproducibility_id",
        "artifact_id",
        "node_id",
        "path",
        "reproducibility_path",
    ),
}

_PACKET_SECTION_TYPES = (
    ("metrics", "metrics", ResearchArtifactGraphBuilder._metrics_id),
    ("data_quality", "data_quality", ResearchArtifactGraphBuilder._data_quality_id),
    (
        "reproducibility",
        "reproducibility",
        ResearchArtifactGraphBuilder._reproducibility_id,
    ),
)

__all__ = [
    "ResearchArtifactEdge",
    "ResearchArtifactGraph",
    "ResearchArtifactGraphBuilder",
    "ResearchArtifactGraphWriter",
    "ResearchArtifactNode",
]
