"""Canonical, renderer-independent design and project models."""
from __future__ import annotations

from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SemanticRole(StrEnum):
    THESIS = "thesis"
    EVIDENCE = "evidence"
    METRIC = "metric"
    CATEGORY = "category"
    ACTION = "action"
    CONTEXT = "context"
    CAVEAT = "caveat"
    LABEL = "label"


class Importance(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceStatus(StrEnum):
    VERIFIED = "verified"
    USER_SUPPLIED = "user_supplied"
    ILLUSTRATIVE = "illustrative"
    UNKNOWN = "unknown"


class RelationType(StrEnum):
    SEQUENCE = "sequence"
    HIERARCHY = "hierarchy"
    COMPARISON = "comparison"
    CAUSALITY = "causality"
    CYCLE = "cycle"
    NETWORK = "network"
    COMPOSITION = "composition"
    DISTRIBUTION = "distribution"
    SUPPORTS = "supports"
    HANDOFF = "handoff"


class Canvas(StrictModel):
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    unit: Literal["in", "pt", "px"] = "in"


class PageMessage(StrictModel):
    thesis: str = Field(min_length=1)
    audience: str = ""
    purpose: str = ""
    reading_path: list[str] = Field(default_factory=list)


class Geometry(StrictModel):
    """Position and size in canvas units; renderer converts to inches."""
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class DesignNode(StrictModel):
    id: str = Field(min_length=1)
    text: str
    semantic_role: SemanticRole
    importance: Importance = Importance.MEDIUM
    evidence_status: EvidenceStatus = EvidenceStatus.UNKNOWN
    reading_order: int = 0
    source_ref: str | None = None
    data_ref: str | None = None
    geometry: Geometry | None = None
    visual_type: Literal["text", "rect", "ellipse"] = "text"
    font_size_pt: float = Field(default=18, gt=0)
    color: str = "#282126"
    fill: str | None = None
    align: Literal["left", "center", "right"] = "left"


class DesignRelation(StrictModel):
    id: str = Field(min_length=1)
    from_: str = Field(alias="from", min_length=1)
    to: str = Field(min_length=1)
    relation_type: RelationType
    direction: Literal["forward", "reverse", "bidirectional", "none"] = "none"
    label: str = ""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, validate_assignment=True)


class DesignConstraints(StrictModel):
    density: Literal["low", "medium", "high"] = "medium"
    min_font_pt: float = Field(default=12, gt=0)
    style_dna_ref: str = "GCL"
    allow_gradients: bool = False
    allow_shadows: bool = False


class DesignIR(StrictModel):
    deck_id: str = Field(min_length=1)
    slide_id: str = Field(min_length=1)
    canvas: Canvas = Field(default_factory=lambda: Canvas(width=13.333, height=7.5, unit="in"))
    message: PageMessage
    nodes: list[DesignNode] = Field(default_factory=list)
    relations: list[DesignRelation] = Field(default_factory=list)
    constraints: DesignConstraints = Field(default_factory=DesignConstraints)

    @model_validator(mode="after")
    def validate_references(self) -> "DesignIR":
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Design node IDs must be unique")
        known = set(ids)
        for relation in self.relations:
            if relation.from_ not in known or relation.to not in known:
                raise ValueError(f"Relation {relation.id!r} references an unknown node")
        for node in self.nodes:
            if node.semantic_role == SemanticRole.METRIC and not node.data_ref:
                raise ValueError(f"Metric node {node.id!r} must use a DataLedger data_ref")
            if node.geometry:
                g = node.geometry
                if g.x + g.width > self.canvas.width or g.y + g.height > self.canvas.height:
                    raise ValueError(f"Node {node.id!r} exceeds canvas bounds")
        return self


class PageStatus(StrEnum):
    PLANNED = "planned"
    CONTENT_APPROVED = "content_approved"
    DESIGN_APPROVED = "design_approved"
    RENDERED = "rendered"
    QA_PASSED = "qa_passed"
    DELIVERED = "delivered"
    CONTENT_REWORK = "content_rework"
    DESIGN_REWORK = "design_rework"
    RENDER_REWORK = "render_rework"
    QA_REJECTED = "qa_rejected"


class PageRecord(StrictModel):
    slide_id: str
    status: PageStatus = PageStatus.PLANNED
    version: int = 1
    issues: list[str] = Field(default_factory=list)


class ProjectState(StrictModel):
    project_id: str
    pages: dict[str, PageRecord] = Field(default_factory=dict)
    revision: int = 0
