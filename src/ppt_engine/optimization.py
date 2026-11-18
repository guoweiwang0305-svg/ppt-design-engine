"""P0.11 layout optimization and explainable visual critic.

The optimizer applies only low-risk deterministic repairs. It never changes copy,
semantic relations, chart meaning, or node order; those require a design/content decision.
"""
from __future__ import annotations

from typing import Literal
from pydantic import Field

from .models import DesignIR, StrictModel
from .visual_qa import VisualQAReport, audit_design_ir


class RepairAction(StrictModel):
    code: str
    node_id: str
    before: str
    after: str
    rationale: str


class CriticFinding(StrictModel):
    code: str
    severity: Literal["blocker", "major", "minor", "info"]
    node_ids: list[str] = Field(default_factory=list)
    diagnosis: str
    recommendation: str
    auto_repairable: bool = False


class VisualCriticReport(StrictModel):
    slide_id: str
    decision: Literal["accept_for_human_review", "revise", "blocked"]
    findings: list[CriticFinding] = Field(default_factory=list)
    repair_actions: list[RepairAction] = Field(default_factory=list)
    iterations: int = 0
    human_review_required: bool = True
    limitations: list[str] = Field(default_factory=lambda: [
        "No OCR or vision-language model is used to judge rendered typography or aesthetics.",
        "Text-fit estimates are heuristic; inspect rendered PNG at 100% zoom.",
        "Semantic correctness, narrative quality and brand fidelity require human review.",
    ])


class OptimizationResult(StrictModel):
    design_ir: DesignIR
    report: VisualCriticReport


def _text_capacity(node, canvas_unit: str) -> tuple[int, int]:
    g = node.geometry
    if g is None:
        return 0, 0
    scale = 72 if canvas_unit == "in" else (1 if canvas_unit == "pt" else 0.75)
    width_pt, height_pt = g.width * scale, g.height * scale
    chars_per_line = max(1, int((width_pt - 8) / max(1, node.font_size_pt * 0.52)))
    estimated_lines = sum(max(1, (len(line) + chars_per_line - 1) // chars_per_line)
                          for line in (node.text.splitlines() or [""]))
    available_lines = max(1, int(max(0, height_pt - 5) / max(1, node.font_size_pt * 1.22)))
    return estimated_lines, available_lines


def _critic(ir: DesignIR, qa: VisualQAReport) -> list[CriticFinding]:
    findings: list[CriticFinding] = []
    for issue in qa.issues:
        if issue.code == "missing_geometry":
            findings.append(CriticFinding(code=issue.code, severity="blocker",
                node_ids=issue.node_ids, diagnosis=issue.message,
                recommendation="Return to the layout planner and assign explicit geometry.",
                auto_repairable=False))
        elif issue.code == "element_overlap":
            findings.append(CriticFinding(code=issue.code, severity="major",
                node_ids=issue.node_ids, diagnosis=issue.message,
                recommendation="Recompose the affected slots; preserve reading order and relation endpoints.",
                auto_repairable=False))
        elif issue.code in ("possible_text_overflow", "font_below_minimum"):
            findings.append(CriticFinding(code=issue.code, severity="major",
                node_ids=issue.node_ids, diagnosis=issue.message,
                recommendation="Reduce copy or enlarge/reflow the slot; font reduction is allowed only down to the configured minimum.",
                auto_repairable=True))
        else:
            findings.append(CriticFinding(code=issue.code, severity="minor",
                node_ids=issue.node_ids, diagnosis=issue.message,
                recommendation="Inspect the rendered slide and adjust the source layout if the issue is visible.",
                auto_repairable=False))
    # Focal dominance proxy: compare text area-weighted importance, not visual saliency.
    positioned = [n for n in ir.nodes if n.geometry is not None]
    if len(positioned) >= 3:
        areas = sorted((n.geometry.width * n.geometry.height for n in positioned), reverse=True)
        total = sum(areas)
        if total and areas[0] / total > 0.72:
            findings.append(CriticFinding(code="single_element_dominance", severity="minor",
                diagnosis="One element occupies more than 72% of the combined node area.",
                recommendation="Check whether the dominant element is the intended thesis/focal visual; otherwise rebalance the composition.",
                auto_repairable=False))
    return findings


def optimize_layout(ir: DesignIR, max_iterations: int = 2,
                    min_font_pt: float | None = None) -> OptimizationResult:
    """Apply bounded font-fit repairs, then produce a critic report.

    Deliberately does not move overlapping nodes automatically: moving a node can
    invalidate causal/sequence relationships and the page's reading path.
    """
    if max_iterations < 0 or max_iterations > 5:
        raise ValueError("max_iterations must be between 0 and 5")
    result = ir.model_copy(deep=True)
    minimum = min_font_pt if min_font_pt is not None else result.constraints.min_font_pt
    actions: list[RepairAction] = []
    iterations = 0

    for _ in range(max_iterations):
        changed = False
        for node in result.nodes:
            if node.geometry is None or not node.text:
                continue
            estimated, available = _text_capacity(node, result.canvas.unit)
            if estimated <= available or node.font_size_pt <= minimum:
                continue
            before = node.font_size_pt
            # Conservative one-point steps; never below the system's minimum.
            node.font_size_pt = max(minimum, round(before - 1, 2))
            actions.append(RepairAction(
                code="shrink_text_to_fit", node_id=node.id,
                before=f"{before:g}pt", after=f"{node.font_size_pt:g}pt",
                rationale="Heuristic text capacity exceeded; reduced one point without crossing the configured minimum.",
            ))
            changed = True
        if not changed:
            break
        iterations += 1

    qa = audit_design_ir(result, min_font_pt=minimum)
    findings = _critic(result, qa)
    if any(f.severity == "blocker" for f in findings):
        decision = "blocked"
    elif any(f.severity in ("major", "minor") for f in findings):
        decision = "revise"
    else:
        decision = "accept_for_human_review"
    return OptimizationResult(
        design_ir=result,
        report=VisualCriticReport(
            slide_id=result.slide_id, decision=decision, findings=findings,
            repair_actions=actions, iterations=iterations, human_review_required=True,
        ),
    )
