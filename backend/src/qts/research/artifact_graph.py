"""Deterministic research artifact relationship graph."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash


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
        """Validate graph references, acyclicity, and required artifact links."""

        nodes_by_id = self._nodes_by_id()
        for edge in self.edges:
            if edge.source_id not in nodes_by_id:
                raise ValueError(f"edge source_id is not a node: {edge.source_id}")
            if edge.target_id not in nodes_by_id:
                raise ValueError(f"edge target_id is not a node: {edge.target_id}")
        self._validate_required_edges(nodes_by_id)
        self._validate_acyclic(nodes_by_id)

    def stable_hash(self) -> str:
        """Return an order-independent stable hash for this graph."""

        return stable_json_hash(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready graph payload."""

        return {
            "edges": [edge.to_payload() for edge in self.edges],
            "nodes": [node.to_payload() for node in self.nodes],
        }

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

    def _validate_required_edges(self, nodes_by_id: Mapping[str, ResearchArtifactNode]) -> None:
        for source_type, target_type, message in _REQUIRED_REFERENCES:
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
        evidence_bundles: Sequence[Mapping[str, Any]] = (),
        promotion_packets: Sequence[Mapping[str, Any]] = (),
        audit_records: Sequence[Mapping[str, Any]] = (),
        reports: Sequence[Mapping[str, Any]] = (),
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

        for promotion_packet in promotion_packets:
            packet_node = self._node(
                promotion_packet,
                "promotion_packet",
                self._promotion_packet_id,
            )
            self._add_node(nodes_by_id, packet_node)
            edges.append(
                ResearchArtifactEdge(
                    source_id=packet_node.node_id,
                    target_id=self._required_text(promotion_packet, "evidence_bundle_id"),
                    relation="references",
                )
            )

        for audit_record in audit_records:
            self._add_node(
                nodes_by_id,
                self._node(audit_record, "audit_record", self._audit_record_id),
            )

        for report in reports:
            report_node = self._node(report, "report", self._report_id)
            report_refs = self._report_refs(report)
            self._add_node(nodes_by_id, report_node)
            edges.append(
                ResearchArtifactEdge(
                    source_id=report_node.node_id,
                    target_id=self._required_text(report_refs, "promotion_packet_id"),
                    relation="references",
                )
            )
            edges.append(
                ResearchArtifactEdge(
                    source_id=report_node.node_id,
                    target_id=self._required_text(report_refs, "audit_record_id"),
                    relation="references",
                )
            )

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

    def _evidence_bundle_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("evidence_bundle_id", "node_id"))

    def _promotion_packet_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(
            payload,
            ("promotion_packet_id", "packet_id", "promotion_candidate_id", "node_id"),
        )

    def _audit_record_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("record_id", "audit_record_id", "node_id"))

    def _report_id(self, payload: Mapping[str, Any]) -> str:
        return self._first_text(payload, ("report_id", "workflow_id", "node_id", "path"))

    def _first_text(self, payload: Mapping[str, Any], field_names: Sequence[str]) -> str:
        for field_name in field_names:
            value = payload.get(field_name)
            if value is not None:
                return self._text(value, field_name)
        raise ValueError(f"{field_names[0]} is required")

    def _required_text(self, payload: Mapping[str, Any], field_name: str) -> str:
        if field_name == "promotion_packet_id":
            return self._first_text(payload, ("promotion_packet_id", "packet_id"))
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
    ) -> WriteResult:
        """Validate and write a deterministic JSON artifact graph payload."""

        graph.validate()
        target = self._resolve_output_path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(stable_json_dumps(graph.to_payload()) + "\n", encoding="utf-8")
        return self.WriteResult(
            path=target,
            artifact_graph_hash=graph.stable_hash(),
            graph=graph,
        )

    def write_from_payloads(
        self,
        *,
        manifests: Sequence[Mapping[str, Any]] = (),
        evidence_bundles: Sequence[Mapping[str, Any]] = (),
        promotion_packets: Sequence[Mapping[str, Any]] = (),
        audit_records: Sequence[Mapping[str, Any]] = (),
        reports: Sequence[Mapping[str, Any]] = (),
        output_path: str | Path = "artifact-graph.json",
    ) -> WriteResult:
        """Build, validate, and persist a graph from artifact payloads."""

        graph = ResearchArtifactGraphBuilder().build(
            manifests=manifests,
            evidence_bundles=evidence_bundles,
            promotion_packets=promotion_packets,
            audit_records=audit_records,
            reports=reports,
        )
        return self.write(graph, output_path=output_path)

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
    }
)

_REQUIRED_REFERENCES = (
    (
        "promotion_packet",
        "evidence_bundle",
        "promotion_packet must reference evidence_bundle",
    ),
    ("evidence_bundle", "manifest", "evidence_bundle must reference manifest"),
    ("report", "promotion_packet", "report must reference promotion_packet"),
    ("report", "audit_record", "report must reference audit_record"),
)

__all__ = [
    "ResearchArtifactEdge",
    "ResearchArtifactGraph",
    "ResearchArtifactGraphBuilder",
    "ResearchArtifactGraphWriter",
    "ResearchArtifactNode",
]
