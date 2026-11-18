"""Reference-slide reverse engineering contracts and deterministic baseline."""
from __future__ import annotations
from typing import Literal
from pydantic import Field
from .intelligence import InformationGraph, InformationNode, InformationEdge, VisualGrammar
from .models import RelationType, StrictModel

class BoundingBox(StrictModel):
    x: float
    y: float
    width: float
    height: float
    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

class VisualElement(StrictModel):
    element_id: str
    kind: Literal["text","shape","line","image","group","icon","unknown"]
    bbox: BoundingBox
    text: str | None = None
    parent_group: str | None = None
    z_index: int = 0
    visual_weight: float = 0.5
    is_decorative: bool = False
    confidence: float = 0.5
    style_tokens: list[str] = Field(default_factory=list)

class Connector(StrictModel):
    connector_id: str
    source_element: str
    target_element: str
    relation_hint: RelationType | None = None
    confidence: float = 0.5
    decorative: bool = False

class VisualHierarchy(StrictModel):
    level: int
    element_ids: list[str]
    rationale: str

class ReferenceVisualPage(StrictModel):
    reference_id: str
    canvas_width: float = 16.0
    canvas_height: float = 9.0
    elements: list[VisualElement] = Field(default_factory=list)
    connectors: list[Connector] = Field(default_factory=list)
    hierarchy: list[VisualHierarchy] = Field(default_factory=list)

class SemanticEvidence(StrictModel):
    source_element_ids: list[str]
    statement: str
    relation: RelationType | None = None
    confidence: float = 0.5
    evidence_type: Literal["text","connector","position","style","group"] = "text"

class ReconstructedDesign(StrictModel):
    information_graph: InformationGraph
    semantic_evidence: list[SemanticEvidence] = Field(default_factory=list)
    ignored_decorative_elements: list[str] = Field(default_factory=list)
    visual_grammar: VisualGrammar | None = None
    reconstruction_confidence: float = 0.0

def reconstruct_information_graph(page: ReferenceVisualPage, thesis: str = "Reconstructed reference page") -> ReconstructedDesign:
    active = [e for e in page.elements if not e.is_decorative and e.kind in {"text","shape","image","icon"}]
    nodes = [InformationNode(id=e.element_id,label=e.text or e.element_id,kind="visual_element",importance="high" if e.visual_weight >= 0.75 else "medium") for e in active]
    known = {e.element_id for e in active}
    edges: list[InformationEdge] = []
    evidence: list[SemanticEvidence] = []
    for c in page.connectors:
        if c.decorative or c.source_element not in known or c.target_element not in known:
            continue
        relation = c.relation_hint or RelationType.HANDOFF
        edges.append(InformationEdge(source=c.source_element,target=c.target_element,relation=relation))
        evidence.append(SemanticEvidence(source_element_ids=[c.source_element,c.target_element],statement=f"Connector indicates {c.source_element} -> {c.target_element}",relation=relation,confidence=c.confidence,evidence_type="connector"))
    graph = InformationGraph(graph_id=f"{page.reference_id}:reconstructed",thesis=thesis,nodes=nodes,edges=edges)
    confidence = sum(e.confidence for e in evidence) / len(evidence) if evidence else 0.25
    return ReconstructedDesign(information_graph=graph,semantic_evidence=evidence,ignored_decorative_elements=[e.element_id for e in page.elements if e.is_decorative],reconstruction_confidence=confidence)

class PatternFeedback(StrictModel):
    pattern_id: str
    reference_id: str
    decision: Literal["accept","reject","revise"]
    reason_codes: list[str] = Field(default_factory=list)
    notes: str = ""
    weight_delta: float = 0.0

class PatternPreferenceProfile(StrictModel):
    profile_id: str
    accepted_patterns: dict[str,float] = Field(default_factory=dict)
    rejected_patterns: dict[str,float] = Field(default_factory=dict)
    revision_notes: dict[str,list[str]] = Field(default_factory=dict)
    def apply(self, feedback: PatternFeedback) -> "PatternPreferenceProfile":
        accepted=dict(self.accepted_patterns); rejected=dict(self.rejected_patterns)
        notes={k:list(v) for k,v in self.revision_notes.items()}; delta=feedback.weight_delta or 1.0
        if feedback.decision=="accept": accepted[feedback.pattern_id]=accepted.get(feedback.pattern_id,0.0)+delta
        elif feedback.decision=="reject": rejected[feedback.pattern_id]=rejected.get(feedback.pattern_id,0.0)+delta
        else: notes.setdefault(feedback.pattern_id,[]).append(feedback.notes or "revise")
        return PatternPreferenceProfile(profile_id=self.profile_id,accepted_patterns=accepted,rejected_patterns=rejected,revision_notes=notes)
    def preference_adjustment(self, pattern_id: str) -> float:
        return self.accepted_patterns.get(pattern_id,0.0)-self.rejected_patterns.get(pattern_id,0.0)

def learn_pattern_adjustment(profile: PatternPreferenceProfile, pattern_id: str, base_score: float) -> float:
    return max(0.0,min(1.0,base_score+0.05*profile.preference_adjustment(pattern_id)))
