"""Deterministic preflight and human visual-review checklist for rendered slides."""
from __future__ import annotations

from typing import Literal
from pydantic import Field
from .models import DesignIR, StrictModel


class QAIssue(StrictModel):
    code: str
    severity: Literal["error", "warning", "info"]
    node_ids: list[str] = Field(default_factory=list)
    message: str


class VisualQAReport(StrictModel):
    slide_id: str
    status: Literal["blocked", "review_required", "preflight_passed"]
    issues: list[QAIssue] = Field(default_factory=list)
    human_review_required: bool = True
    rendered_assets: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)


def _intersection_area(a, b) -> float:
    left, top = max(a.x, b.x), max(a.y, b.y)
    right, bottom = min(a.x + a.width, b.x + b.width), min(a.y + a.height, b.y + b.height)
    return max(0.0, right - left) * max(0.0, bottom - top)


def audit_design_ir(ir: DesignIR, min_font_pt: float | None = None,
                    overlap_warning_ratio: float = 0.12) -> VisualQAReport:
    """Run geometry/font preflight; pixel-level visual judgment remains human-led."""
    issues: list[QAIssue] = []
    minimum = min_font_pt or ir.constraints.min_font_pt
    positioned = [n for n in ir.nodes if n.geometry is not None]
    for node in ir.nodes:
        if node.geometry is None:
            issues.append(QAIssue(
                code="missing_geometry", severity="error", node_ids=[node.id],
                message="Node has no geometry; renderer must not guess its position.",
            ))
        if node.font_size_pt < minimum:
            issues.append(QAIssue(
                code="font_below_minimum", severity="warning", node_ids=[node.id],
                message=f"Font {node.font_size_pt}pt is below configured minimum {minimum}pt.",
            ))
    for index, first in enumerate(positioned):
        for second in positioned[index + 1:]:
            overlap = _intersection_area(first.geometry, second.geometry)
            smaller = min(first.geometry.width * first.geometry.height,
                          second.geometry.width * second.geometry.height)
            ratio = overlap / smaller if smaller else 0
            if ratio >= overlap_warning_ratio:
                issues.append(QAIssue(
                    code="element_overlap", severity="warning",
                    node_ids=[first.id, second.id],
                    message=f"Elements overlap by {ratio:.0%} of the smaller element area.",
                ))
    if any(issue.severity == "error" for issue in issues):
        status = "blocked"
    elif issues:
        status = "review_required"
    else:
        status = "preflight_passed"
    return VisualQAReport(
        slide_id=ir.slide_id, status=status, issues=issues,
        human_review_required=True,
        checklist=[
            "Inspect full-slide PNG at presentation size for reading order and focal hierarchy.",
            "Inspect contact sheet for consistency across adjacent slides.",
            "Check small labels, chart axes, footnotes and source text at 100% zoom.",
            "Check grayscale hierarchy and contrast; do not rely on red alone to encode meaning.",
            "Check chart scales, units, periods, denominators and DataLedger consistency.",
            "Check visual balance, alignment, whitespace and unintended overlaps.",
            "Confirm all images, icons and logos have permitted provenance.",
        ],
    )
