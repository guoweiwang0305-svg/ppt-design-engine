"""Bounded end-to-end quality pass: safe preflight repair, render, then critic."""
from __future__ import annotations
from pathlib import Path
from pydantic import Field
from .models import StrictModel
from .models import DesignIR
from .ledger import DataLedger
from .optimization import optimize_layout, RepairAction
from .advanced_critic import critique_slide, AdvancedCriticReport
from .renderer import render_pptx, export_pdf, export_pngs


class QualityLoopResult(StrictModel):
    design_ir: DesignIR
    pptx_path: str
    pdf_path: str
    png_paths: list[str] = Field(default_factory=list)
    repair_actions: list[RepairAction] = Field(default_factory=list)
    rounds: int
    critic: AdvancedCriticReport
    stopped_reason: str


def run_quality_loop(ir: DesignIR, output_dir: str | Path,
                     max_rounds: int = 4, ledger: DataLedger | None = None) -> QualityLoopResult:
    """Run bounded deterministic repair rounds, render final assets and post-render critique.

    Only text-fit font adjustments are auto-applied. Geometry suggestions, content
    reflow and slide splitting remain explicit decisions for the layout agent/human.
    """
    if not 1 <= max_rounds <= 8:
        raise ValueError("max_rounds must be between 1 and 8")
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    current=ir.model_copy(deep=True)
    actions=[]
    rounds=0
    stopped="max_rounds_reached"
    for _ in range(max_rounds):
        result=optimize_layout(current,max_iterations=1)
        current=result.design_ir
        rounds += 1
        actions.extend(result.report.repair_actions)
        if not result.report.repair_actions:
            stopped="no_safe_repairs_remaining"
            break
    pptx=render_pptx(current,out/f"{current.slide_id}.pptx",ledger=ledger)
    pdf=export_pdf(pptx,out/"pdf")
    pngs=export_pngs(pdf,out/"png")
    critic=critique_slide(current,str(pngs[0]) if pngs else None)
    if critic.decision=="accept_for_human_review":
        stopped="critic_found_no_blocking_or_review_findings"
    elif stopped=="no_safe_repairs_remaining":
        stopped="critic_requires_design_or_human_review"
    return QualityLoopResult(design_ir=current,pptx_path=str(pptx),pdf_path=str(pdf),
        png_paths=[str(p) for p in pngs],repair_actions=actions,rounds=rounds,
        critic=critic,stopped_reason=stopped)
