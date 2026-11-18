"""P0.10 reference-to-production contracts.

This module converts reviewed reference patterns into ranked, fillable layout plans.
It deliberately does not invent geometry: the renderer must resolve slot geometry
from a versioned layout specification or request human intervention.
"""
from __future__ import annotations

from typing import Any, Literal
from pydantic import Field

from .intelligence import InformationGraph, PatternCandidate, CandidateScore, rank_patterns
from .models import Canvas, DesignConstraints, DesignIR, DesignNode, DesignRelation, EvidenceStatus, Geometry, Importance, PageMessage, RelationType, SemanticRole, StrictModel


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
    geometry: Geometry | None = None
    arrangement: Literal["single", "stack", "grid", "horizontal"] = "single"


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
    canvas: Canvas = Field(default_factory=lambda: Canvas(width=13.333, height=7.5, unit="in"))
    slots: list[LayoutSlot]
    assignments: list[SlotAssignment]
    unassigned_node_ids: list[str] = Field(default_factory=list)
    unresolved_relation_ids: list[str] = Field(default_factory=list)
    geometry_status: Literal["needs_layout_resolution", "resolved"] = "needs_layout_resolution"
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


def _slot_matches(slot_id: str, node: Any) -> bool:
    slot = slot_id.lower()
    kind = str(node.kind).lower()
    if "driver" in slot: return "driver" in kind
    if "evidence" in slot or "source" in slot: return kind in ("evidence", "fact", "source", "metric", "kpi")
    if "kpi" in slot or "metric" in slot: return kind in ("metric", "kpi", "number")
    if "region" in slot or "geographic" in slot: return "region" in kind or "geography" in kind
    if "rank" in slot: return kind in ("entity", "competitor", "ranked_entity", "metric")
    if "segment" in slot: return "segment" in kind or "customer" in kind
    if "tag" in slot: return "tag" in kind or "attribute" in kind
    if "touchpoint" in slot: return "touchpoint" in kind or "digital" in kind or "human" in kind
    if "actor" in slot: return kind in ("actor", "partner", "provider", "platform")
    if "flow" in slot: return "flow" in kind or "stream" in kind
    if "pillar" in slot: return kind in ("pillar", "capability", "initiative")
    if "service" in slot: return "service" in kind or kind == "provider"
    if "product" in slot: return "product" in kind or "need" in kind
    if "outcome" in slot or "problem" in slot: return kind in ("outcome", "problem", "thesis")
    if "initiative" in slot or "action" in slot: return kind in ("initiative", "action")
    if "owner" in slot: return kind in ("owner", "role", "team")
    return False


def build_layout_plan(graph: InformationGraph, catalog: dict[str, Any],
                      pattern_id: str, geometry_catalog: dict[str, Any] | None = None) -> LayoutPlan:
    """Bind graph nodes to semantic slots without fabricating final coordinates."""
    entry = next((p for p in catalog.get("layouts", catalog.get("patterns", [])) if p.get("id") == pattern_id), None)
    if entry is None:
        raise KeyError(f"Unknown layout pattern: {pattern_id}")
    raw_slots = entry.get("slots", [])
    geo_entry = (geometry_catalog or {}).get("layouts", {}).get(pattern_id, {})
    geo_slots = geo_entry.get("slots", {})
    nodes = list(graph.nodes)
    assignments: list[SlotAssignment] = []
    used: set[str] = set()
    slots: list[LayoutSlot] = []
    # Conservative semantic mapping. Explicit node kinds win; otherwise reserve
    # the thesis node for the first title-like slot and preserve remaining nodes.
    for index, slot_id in enumerate(raw_slots):
        role = slot_id.replace("_", " ")
        title_only = slot_id in ("headline_conclusion", "comparison_question", "market_scope", "segmentation_basis", "customer_trigger", "geographic_scope")
        required = (index < min(3, len(raw_slots))) and not title_only
        max_items = 1
        spec = geo_slots.get(slot_id, {})
        geometry = Geometry.model_validate(spec["geometry"]) if spec.get("geometry") else None
        arrangement = spec.get("arrangement", "single")
        max_items = int(spec.get("max_items", max_items))
        if arrangement == "single" and max_items > 1:
            arrangement = "grid"
        slot = LayoutSlot(
            slot_id=slot_id, role=role, required=required, min_items=1 if required else 0,
            max_items=max_items, geometry_token=f"{pattern_id}.{slot_id}",
            geometry=geometry, arrangement=arrangement,
        )
        slots.append(slot)
        if title_only:
            assignments.append(SlotAssignment(slot_id=slot_id, status="empty_optional",
                note="Page thesis is rendered in the dedicated thesis node."))
            continue
        if title_only:
            assignments.append(SlotAssignment(slot_id=slot_id, status="empty_optional",
                note="Page thesis is rendered in the dedicated thesis node."))
            continue
        candidates = [n for n in nodes if n.id not in used]
        if not candidates:
            assignments.append(SlotAssignment(
                slot_id=slot_id, status="missing_required" if required else "empty_optional",
                note="No unassigned InformationNode available.",
            ))
            continue
        matched = [n for n in candidates if _slot_matches(slot_id, n)]
        chosen = (matched or candidates)[:max_items]
        used.update(n.id for n in chosen)
        assignments.append(SlotAssignment(
            slot_id=slot_id, node_ids=[n.id for n in chosen], status="filled",
            note="Provisional binding; confirm semantic fit during content review.",
        ))
    missing_geometry = [s.slot_id for s in slots if s.geometry is None]
    warnings = []
    if missing_geometry:
        warnings.append("Missing geometry for slots: " + ", ".join(missing_geometry))
    if any(a.status == "missing_required" for a in assignments):
        warnings.append("Required semantic slots are unfilled.")
    if graph.edges:
        warnings.append("Relations are preserved; connector routing still requires layout routing.")
    if any(n.id not in used for n in nodes):
        warnings.append("Some InformationGraph nodes remain unassigned.")
    return LayoutPlan(
        pattern_id=pattern_id, layout_id=pattern_id, graph_id=graph.graph_id,
        thesis=graph.thesis, slots=slots, assignments=assignments,
        unassigned_node_ids=[n.id for n in nodes if n.id not in used],
        unresolved_relation_ids=[f"{e.source}->{e.target}:{e.relation.value}" for e in graph.edges],
        geometry_status="resolved" if not missing_geometry else "needs_layout_resolution",
        warnings=warnings,
    )


def _split_slot_geometry(g: Geometry, count: int, arrangement: str) -> list[Geometry]:
    if count <= 1:
        return [g]
    gap = 0.12
    if arrangement == "horizontal":
        w = (g.width - gap * (count - 1)) / count
        return [Geometry(x=g.x+i*(w+gap), y=g.y, width=w, height=g.height) for i in range(count)]
    if arrangement == "grid":
        cols = 2 if count <= 4 else 3
        rows = (count + cols - 1) // cols
        w = (g.width - gap * (cols-1)) / cols
        h = (g.height - gap * (rows-1)) / rows
        return [Geometry(x=g.x+(i%cols)*(w+gap), y=g.y+(i//cols)*(h+gap), width=w, height=h) for i in range(count)]
    h = (g.height - gap * (count-1)) / count
    return [Geometry(x=g.x, y=g.y+i*(h+gap), width=g.width, height=h) for i in range(count)]


def layout_plan_to_design_ir(graph: InformationGraph, plan: LayoutPlan,
                             min_font_pt: float = 12, style_dna_ref: str = "generali_corporate") -> DesignIR:
    if plan.geometry_status != "resolved":
        raise ValueError("Layout geometry is unresolved; refusing to invent positions.")
    by_id = {n.id: n for n in graph.nodes}
    nodes: list[DesignNode] = []
    used: set[str] = set()
    title_slot = next((s for s in plan.slots if s.slot_id in
        ("headline_conclusion", "comparison_question", "market_scope", "segmentation_basis", "customer_trigger")), None)
    title_geometry = title_slot.geometry if title_slot and title_slot.geometry else Geometry(x=.55, y=.25, width=12.2, height=.55)
    nodes.append(DesignNode(id="page_thesis", text=graph.thesis, semantic_role=SemanticRole.THESIS,
        importance=Importance.CRITICAL, reading_order=0, geometry=title_geometry,
        font_size_pt=24, color="#C00000", align="left"))
    order = 1
    for slot in plan.slots:
        if slot.geometry is None:
            continue
        assignment = next((a for a in plan.assignments if a.slot_id == slot.slot_id), None)
        if not assignment:
            continue
        ids = [nid for nid in assignment.node_ids if nid in by_id and nid not in used]
        if not ids:
            continue
        geos = _split_slot_geometry(slot.geometry, len(ids), slot.arrangement)
        for nid, geo in zip(ids, geos):
            source = by_id[nid]
            kind = source.kind.lower()
            if kind in ("metric", "kpi", "number") and not source.data_ref:
                raise ValueError(f"Metric node {nid!r} requires a DataLedger data_ref.")
            role = (SemanticRole.METRIC if kind in ("metric", "kpi", "number") else
                    SemanticRole.ACTION if kind in ("action", "initiative") else
                    SemanticRole.CATEGORY if kind in ("category", "segment", "stage", "actor") else
                    SemanticRole.EVIDENCE if kind in ("evidence", "fact", "source") else SemanticRole.CONTEXT)
            importance = {"critical": Importance.CRITICAL, "high": Importance.HIGH,
                          "medium": Importance.MEDIUM, "low": Importance.LOW}.get(source.importance, Importance.MEDIUM)
            nodes.append(DesignNode(id=nid, text=source.label, semantic_role=role,
                importance=importance,
                evidence_status=EvidenceStatus.USER_SUPPLIED if source.evidence_ref else EvidenceStatus.UNKNOWN,
                reading_order=order, source_ref=source.evidence_ref, data_ref=source.data_ref,
                geometry=geo, font_size_pt=18 if importance in (Importance.CRITICAL, Importance.HIGH) else 14,
                color="#C00000" if importance in (Importance.CRITICAL, Importance.HIGH) else "#333333",
                fill="#FBF3F3" if role == SemanticRole.CATEGORY else None))
            used.add(nid)
            order += 1
    relations = []
    for i, edge in enumerate(graph.edges, 1):
        if edge.source in used and edge.target in used:
            relations.append(DesignRelation(id=f"rel-{i}", **{"from": edge.source, "to": edge.target},
                relation_type=edge.relation, direction=edge.direction, label=edge.label))
    return DesignIR(deck_id=graph.graph_id, slide_id=plan.layout_id, canvas=plan.canvas,
        message=PageMessage(thesis=graph.thesis, reading_path=[n.id for n in sorted(nodes, key=lambda x:x.reading_order)]),
        nodes=nodes, relations=relations,
        constraints=DesignConstraints(density="high", min_font_pt=min_font_pt, style_dna_ref=style_dna_ref))
