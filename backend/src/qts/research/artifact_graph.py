"""Deterministic research artifact relationship graph."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from qts.core.hashing import stable_json_hash


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
    "ResearchArtifactNode",
]
