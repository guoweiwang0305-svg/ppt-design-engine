"""Information-to-visual intelligence: graph analysis, pattern retrieval and ranking."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from .models import StrictModel, RelationType
from pydantic import Field


class InformationNode(StrictModel):
    id: str
    label: str
    kind: str = "concept"
    importance: str = "medium"
    evidence_ref: str | None = None


class InformationEdge(StrictModel):
    source: str
    target: str
    relation: RelationType
    direction: str = "forward"
    label: str = ""


class InformationGraph(StrictModel):
    graph_id: str
    thesis: str
    nodes: list[InformationNode] = Field(default_factory=list)
    edges: list[InformationEdge] = Field(default_factory=list)

    def validate_graph(self) -> list[str]:
        errors: list[str] = []
        ids = [n.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            errors.append("Information node IDs must be unique")
        known = set(ids)
        for edge in self.edges:
            if edge.source not in known or edge.target not in known:
                errors.append(f"Edge {edge.source}->{edge.target} references unknown node")
        return errors

    def relation_profile(self) -> dict[str, int]:
        profile: dict[str, int] = {}
        for edge in self.edges:
            profile[edge.relation.value] = profile.get(edge.relation.value, 0) + 1
        return profile

    def node_count(self) -> int:
        return len(self.nodes)


class VisualGrammar(StrictModel):
    grammar_id: str
    semantic_family: str
    supported_relations: list[RelationType]
    composition: str
    reading_direction: str = "top_down"
    density: str = "medium"
    hierarchy_levels: int = 3
    preferred_edge_routing: str = "orthogonal"
    style_tokens: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)


class PatternCandidate(StrictModel):
    pattern_id: str
    name: str
    semantic_families: list[str]
    relation_types: list[RelationType]
    min_nodes: int = 2
    max_nodes: int = 24
    density: str = "medium"
    layouts: list[str] = Field(default_factory=list)
    visual_grammar_ref: str
    tags: list[str] = Field(default_factory=list)


class CandidateScore(StrictModel):
    pattern_id: str
    layout: str
    semantic_fit: float
    capacity_fit: float
    relation_fit: float
    density_fit: float
    total: float
    reasons: list[str] = Field(default_factory=list)


def infer_semantic_families(graph: InformationGraph) -> set[str]:
    """Rule-based baseline. LLM enrichment can be plugged in without changing contracts."""
    if graph.validate_graph():
        raise ValueError("; ".join(graph.validate_graph()))
    relations = set(graph.relation_profile())
    families: set[str] = set()
    mapping = {
        "sequence": "process", "hierarchy": "hierarchy", "comparison": "comparison",
        "causality": "causal", "cycle": "cycle", "network": "network",
        "composition": "composition", "distribution": "distribution",
        "supports": "argument", "handoff": "process",
    }
    for relation in relations:
        if relation in mapping:
            families.add(mapping[relation])
    if not families:
        families.add("list_or_taxonomy")
    return families


def rank_patterns(
    graph: InformationGraph,
    patterns: list[PatternCandidate],
    requested_density: str = "high",
    top_k: int = 5,
) -> list[CandidateScore]:
    """Rank semantically compatible patterns; scores are transparent heuristics, not aesthetics."""
    errors = graph.validate_graph()
    if errors:
        raise ValueError("; ".join(errors))
    families = infer_semantic_families(graph)
    relation_set = set(graph.relation_profile())
    results: list[CandidateScore] = []
    for pattern in patterns:
        family_overlap = families.intersection(pattern.semantic_families)
        supported = {r.value for r in pattern.relation_types}
        relation_overlap = relation_set.intersection(supported)
        family_score = len(family_overlap) / max(1, len(families))
        relation_score = len(relation_overlap) / max(1, len(relation_set))
        n = graph.node_count()
        if pattern.min_nodes <= n <= pattern.max_nodes:
            capacity_score = 1.0
        else:
            capacity_score = max(0.0, 1.0 - min(abs(n-pattern.min_nodes), abs(n-pattern.max_nodes))/max(1, pattern.max_nodes))
        density_score = 1.0 if pattern.density == requested_density else (0.7 if pattern.density == "high" and requested_density == "medium" else 0.5)
        total = 0.40*family_score + 0.30*relation_score + 0.20*capacity_score + 0.10*density_score
        reasons = [
            f"semantic families matched: {', '.join(sorted(family_overlap)) or 'none'}",
            f"relation coverage: {len(relation_overlap)}/{len(relation_set)}",
            f"node capacity: {pattern.min_nodes}-{pattern.max_nodes} for {n} nodes",
            f"density preference: {pattern.density} vs requested {requested_density}",
        ]
        for layout in pattern.layouts:
            results.append(CandidateScore(
                pattern_id=pattern.pattern_id, layout=layout,
                semantic_fit=round(family_score, 3), capacity_fit=round(capacity_score, 3),
                relation_fit=round(relation_score, 3), density_fit=round(density_score, 3),
                total=round(total, 3), reasons=reasons,
            ))
    return sorted(results, key=lambda x: x.total, reverse=True)[:top_k]
