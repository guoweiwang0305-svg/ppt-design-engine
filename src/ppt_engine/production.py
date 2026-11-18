"""P0.10 reference-to-production contracts.

This module converts reviewed reference patterns into ranked, fillable layout plans.
It deliberately does not invent geometry: the renderer must resolve slot geometry
from a versioned layout specification or request human intervention.
"""
from __future__ import annotations

from typing import Any, Literal
from pydantic import Field

from .intelligence import InformationGraph, PatternCandidate, CandidateScore, rank_patterns
from .models import RelationType, StrictModel


QUALITY_WEIGHTS = {
    "logic": 0.20,
    "information_value": 0.20,
    "visual_hierarchy": 0.15,
    "density_efficiency": 0.15,
    "chart_or_diagram_quality": 0.10,
    "reusability": 0.15,
    "source_traceability": 0.05,
}


class PageQualityScores(StrictModel):
    logic: float
    information_value: float
    visual_hierarchy: float
    density_efficiency: float
    chart_or_diagram_quality: float
    reusability: float
    source_traceability: float


class PageQualityReview(StrictModel):
    reference_id: str
    scores: PageQualityScores
    weighted_total: float
    decision: Literal["recommended", "revise", "reject"]
    review_status: Literal["unreviewed", "human_reviewed", "approved"] = "unreviewed"
    evidence: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    reviewer_notes: str = ""
    reviewer: str | None = None


class LayoutSlot(StrictModel):
    slot_id: str
    role: str
    required: bool = True
    min_items: int = 0
    max_items: int = 1
    accepted_node_kinds: list[str] = Field(default_factory=list)
    geometry_token: str


class SlotAssignment(StrictModel):
    slot_id: str
    node_ids: list[str] = Field(default_factory=list)
    status: Literal["filled", "empty_optional", "missing_required", "over_capacity"]
    note: str = ""


class LayoutPlan(StrictModel):
    pattern_id: str
    layout_id: str
    graph_id: str
    thesis: str
    slots: list[LayoutSlot]
    assignments: list[SlotAssignment]
    unassigned_node_ids: list[str] = Field(default_factory=list)
    unresolved_relation_ids: list[str] = Field(default_factory=list)
    geometry_status: Literal["needs_layout_resolution"] = "needs_layout_resolution"
    warnings: list[str] = Field(default_factory=list)


class LayoutSelection(StrictModel):
    scores: list[CandidateScore]
    selected_pattern_id: str | None = None
    selected_layout_id: str | None = None
    rationale: list[str] = Field(default_factory=list)


def score_page(reference_id: str, scores: PageQualityScores, evidence: list[str] | None = None,
               risks: list[str] | None = None, review_status: str = "unreviewed",
               reviewer: str | None = None, reviewer_notes: str = "") -> PageQualityReview:
    """Calculate a transparent weighted score; approval remains a human decision."""
    values = scores.model_dump()
    for key, value in values.items():
        if not 0 <= value <= 5:
            raise ValueError(f"{key} must be between 0 and 5")
    total = round(sum(values[k] * weight for k, weight in QUALITY_WEIGHTS.items()), 3)
    risk_items = risks or []
    if total >= 4.2:
        decision = "recommended"
    elif total >= 3.2:
        decision = "revise"
    else:
        decision = "reject"
    # A factual, compliance, provenance or legibility risk blocks recommendation.
    blocking = any(token in " ".join(risk_items).lower()
                   for token in ("factual", "compliance", "unreadable", "illegible", "untraceable"))
    if blocking and decision == "recommended":
        decision = "revise"
    return PageQualityReview(
        reference_id=reference_id, scores=scores, weighted_total=total,
        decision=decision, review_status=review_status, evidence=evidence or [],
        risks=risk_items, reviewer=reviewer, reviewer_notes=reviewer_notes,
    )


def catalog_candidates(catalog: dict[str, Any]) -> list[PatternCandidate]:
    """Convert Generali catalog entries to the existing graph ranker contract."""
    candidates: list[PatternCandidate] = []
    valid_relations = {item.value for item in RelationType}
    for item in catalog.get("layouts", catalog.get("patterns", [])):
        relations = [r for r in item.get("relations", []) if r in valid_relations]
        capacity = item.get("capacity", {})
        def collect_ranges(value: Any) -> list[list[int]]:
            found: list[list[int]] = []
            if isinstance(value, list) and len(value) == 2 and all(isinstance(x, int) for x in value):
                found.append(value)
            elif isinstance(value, dict):
                for child in value.values():
                    found.extend(collect_ranges(child))
            elif isinstance(value, list):
                for child in value:
                    found.extend(collect_ranges(child))
            return found
        ranges = collect_ranges(capacity)
        min_nodes = min((v[0] for v in ranges), default=2)
        max_nodes = max((v[1] for v in ranges), default=24)
        candidates.append(PatternCandidate(
            pattern_id=item["id"], name=item["name"],
            semantic_families=item.get("semantic_families", []),
            relation_types=[RelationType(r) for r in relations],
            min_nodes=max(1, min_nodes), max_nodes=max(1, max_nodes),
            density=item.get("density", "medium"),
            layouts=[item["id"]],
            visual_grammar_ref=item.get("id", "unresolved"),
            tags=item.get("tags", []),
        ))
    return candidates


def select_layout(graph: InformationGraph, catalog: dict[str, Any],
                  requested_density: str = "high", top_k: int = 8) -> LayoutSelection:
    candidates = catalog_candidates(catalog)
    scores = rank_patterns(graph, candidates, requested_density=requested_density, top_k=top_k)
    if not scores:
        return LayoutSelection(scores=[], rationale=["No compatible catalog pattern was found."])
    best = scores[0]
    return LayoutSelection(
        scores=scores, selected_pattern_id=best.pattern_id,
        selected_layout_id=best.layout,
        rationale=best.reasons + [
            "Selection is based on semantic and capacity heuristics, not visual embeddings.",
            "Geometry remains unresolved until the selected layout's slot geometry is loaded.",
        ],
    )


def build_layout_plan(graph: InformationGraph, catalog: dict[str, Any],
                      pattern_id: str) -> LayoutPlan:
    """Bind graph nodes to semantic slots without fabricating final coordinates."""
    entry = next((p for p in catalog.get("layouts", catalog.get("patterns", [])) if p.get("id") == pattern_id), None)
    if entry is None:
        raise KeyError(f"Unknown layout pattern: {pattern_id}")
    raw_slots = entry.get("slots", [])
    nodes = list(graph.nodes)
    assignments: list[SlotAssignment] = []
    used: set[str] = set()
    slots: list[LayoutSlot] = []
    # Conservative semantic mapping. Explicit node kinds win; otherwise reserve
    # the thesis node for the first title-like slot and preserve remaining nodes.
    for index, slot_id in enumerate(raw_slots):
        role = slot_id.replace("_", " ")
        required = index < min(3, len(raw_slots))
        max_items = max(1, len(nodes)) if index == len(raw_slots) - 1 else 1
        slot = LayoutSlot(
            slot_id=slot_id, role=role, required=required, min_items=1 if required else 0,
            max_items=max_items, geometry_token=f"{pattern_id}.{slot_id}",
        )
        slots.append(slot)
        candidates = [n for n in nodes if n.id not in used]
        if not candidates:
            assignments.append(SlotAssignment(
                slot_id=slot_id, status="missing_required" if required else "empty_optional",
                note="No unassigned InformationNode available.",
            ))
            continue
        chosen = candidates[:max_items] if index == len(raw_slots) - 1 else candidates[:1]
        used.update(n.id for n in chosen)
        assignments.append(SlotAssignment(
            slot_id=slot_id, node_ids=[n.id for n in chosen], status="filled",
            note="Provisional binding; confirm semantic fit during content review.",
        ))
    return LayoutPlan(
        pattern_id=pattern_id, layout_id=pattern_id, graph_id=graph.graph_id,
        thesis=graph.thesis, slots=slots, assignments=assignments,
        unassigned_node_ids=[n.id for n in nodes if n.id not in used],
        unresolved_relation_ids=[f"{e.source}->{e.target}:{e.relation.value}"
                                 for e in graph.edges],
        warnings=[
            "Slot assignments are provisional semantic placeholders, not final geometry.",
            "All graph edges remain unresolved until connector routing is designed.",
            "A human must verify slot meaning, reading order and evidence placement.",
        ],
    )
