"""Command-line interface."""
import json
from pathlib import Path

import typer

from .intelligence import InformationGraph, PatternCandidate, rank_patterns
from .ledger import DataLedger
from .models import DesignIR, PageStatus
from .orchestrator import Orchestrator
from .renderer import export_pdf, export_pngs, render_pptx
from .pptx_parser import parse_pptx_to_json
from .mining import PatternReview, apply_pattern_reviews, mine_patterns, save_pattern_review
from .visual_intelligence import extract_visual_features
from .production import PageQualityScores, score_page, select_layout, build_layout_plan, layout_plan_to_design_ir
from .visual_qa import audit_design_ir

app = typer.Typer(help="PPT Design Engine — design intelligence and rendering tools")
project_app = typer.Typer(help="Project lifecycle commands")
ledger_app = typer.Typer(help="DataLedger commands")
app.add_typer(project_app, name="project")
app.add_typer(ledger_app, name="ledger")


@app.command()
def validate(ir_file: Path):
    """Validate a Design IR JSON document."""
    ir = DesignIR.model_validate_json(ir_file.read_text(encoding="utf-8"))
    typer.echo(f"VALID {ir.deck_id}/{ir.slide_id}: {len(ir.nodes)} nodes, {len(ir.relations)} relations")


@app.command()
def render(ir_file: Path, output: Path = Path("build/deck.pptx")):
    """Render one Design IR page to editable PPTX."""
    ir = DesignIR.model_validate_json(ir_file.read_text(encoding="utf-8"))
    typer.echo(str(render_pptx(ir, output)))


@app.command()
def export(pptx_file: Path, output_dir: Path = Path("build/export")):
    """Export PPTX to PDF and per-page PNG (requires LibreOffice + Poppler)."""
    pdf = export_pdf(pptx_file, output_dir)
    images = export_pngs(pdf, output_dir / "png")
    typer.echo(json.dumps({"pdf": str(pdf), "png": [str(p) for p in images]}, ensure_ascii=False, indent=2))


@project_app.command("add-page")
def add_page(slide_id: str, state_file: Path = Path(".engine/project.json")):
    page = Orchestrator(state_file).add_page(slide_id)
    typer.echo(f"{page.slide_id}: {page.status.value}")


@project_app.command("transition")
def transition(slide_id: str, target: PageStatus, state_file: Path = Path(".engine/project.json")):
    page = Orchestrator(state_file).transition(slide_id, target)
    typer.echo(f"{page.slide_id}: {page.status.value} (v{page.version})")


@ledger_app.command("check")
def ledger_check(ledger_file: Path, refs_file: Path):
    ledger = DataLedger.load(ledger_file)
    refs = json.loads(refs_file.read_text(encoding="utf-8"))
    errors = ledger.validate_references(refs)
    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(1)
    typer.echo("DataLedger references valid")



@app.command("parse-pptx")
def parse_pptx_command(
    pptx_file: Path,
    output: Path = Path("build/reference/reference.json"),
):
    """Extract editable slide elements, geometry, text styles and connectors from PPTX."""
    typer.echo(str(parse_pptx_to_json(pptx_file, output)))


@app.command("rank-patterns")
def rank_patterns_command(
    graph_file: Path,
    pattern_dir: Path = Path("visual_patterns"),
    density: str = "high",
    top_k: int = 8,
):
    """Rank visual patterns for an Information Graph and explain the scores."""
    patterns = [
        PatternCandidate.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(pattern_dir.rglob("*.json"))
    ]
    graph = InformationGraph.model_validate_json(graph_file.read_text(encoding="utf-8"))
    ranked = rank_patterns(graph, patterns, requested_density=density, top_k=top_k)
    typer.echo(json.dumps([item.model_dump(mode="json") for item in ranked],
                          ensure_ascii=False, indent=2))


@app.command("mine-patterns")
def mine_patterns_command(
    parsed_files: list[Path] = typer.Argument(..., exists=True, readable=True),
    output: Path = Path("build/pattern_mining/candidates.json"),
    min_frequency: int = 2,
    review_ledger: Path = Path("build/pattern_mining/reviews.jsonl"),
):
    """Mine recurring structural slide patterns from parsed PPTX JSON files."""
    patterns = mine_patterns(parsed_files, min_frequency=min_frequency)
    patterns = apply_pattern_reviews(patterns, review_ledger)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([p.model_dump(mode="json") for p in patterns],
                                 ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"Mined {len(patterns)} candidate patterns -> {output}")


@app.command("review-pattern")
def review_pattern_command(
    pattern_id: str,
    decision: str = typer.Option(..., help="accept, reject, or revise"),
    notes: str = "",
    reviewer: str = "expert",
    revised_name: str = "",
    revised_family: str = "",
    ledger: Path = Path("build/pattern_mining/reviews.jsonl"),
):
    """Record an append-only expert decision for a mined pattern."""
    review = PatternReview(
        pattern_id=pattern_id, decision=decision, notes=notes, reviewer=reviewer,
        revised_name=revised_name or None, revised_family=revised_family or None,
    )
    save_pattern_review(review, ledger)
    typer.echo(f"Recorded {decision} for {pattern_id} -> {ledger}")


@app.command("extract-visual-features")
def extract_visual_features_command(
    parsed_files: list[Path] = typer.Argument(..., exists=True, readable=True),
    output: Path = Path("build/visual_intelligence/features.json"),
):
    """Extract explainable geometry, whitespace, typography and palette features."""
    features = []
    for source in parsed_files:
        data = json.loads(source.read_text(encoding="utf-8"))
        features.extend(item.model_dump(mode="json") for item in extract_visual_features(data))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(features, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"Extracted {len(features)} slide feature vectors -> {output}")



@app.command("score-page")
def score_page_command(
    review_file: Path,
    output: Path = Path("build/reference_reviews/page_review.json"),
):
    """Calculate a page's weighted score from explicit human-entered dimensions."""
    payload = json.loads(review_file.read_text(encoding="utf-8"))
    scores = PageQualityScores.model_validate(payload["scores"])
    review = score_page(
        reference_id=payload["reference_id"], scores=scores,
        evidence=payload.get("evidence", []), risks=payload.get("risks", []),
        review_status=payload.get("review_status", "unreviewed"),
        reviewer=payload.get("reviewer"), reviewer_notes=payload.get("reviewer_notes", ""),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(review.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"{review.reference_id}: {review.weighted_total}/5 ({review.decision}) -> {output}")


@app.command("select-layout")
def select_layout_command(
    graph_file: Path,
    catalog_file: Path = Path("visual_patterns/generali/insurance_layout_catalog.json"),
    density: str = "high",
    top_k: int = 8,
    output: Path = Path("build/layout_selection.json"),
):
    """Select Generali insurance layouts from an Information Graph."""
    graph = InformationGraph.model_validate_json(graph_file.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    result = select_layout(graph, catalog, requested_density=density, top_k=top_k)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(result.model_dump_json(indent=2))


@app.command("build-layout-plan")
def build_layout_plan_command(
    graph_file: Path,
    pattern_id: str,
    catalog_file: Path = Path("visual_patterns/generali/insurance_layout_catalog.json"),
    output: Path = Path("build/layout_plan.json"),
):
    """Bind Information Graph nodes to editable semantic layout slots."""
    graph = InformationGraph.model_validate_json(graph_file.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    plan = build_layout_plan(graph, catalog, pattern_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Layout plan -> {output}")
\n\n

@app.command("audit-design-ir")
def audit_design_ir_command(
    ir_file: Path,
    output: Path = Path("build/qa/preflight.json"),
):
    """Run deterministic geometry/font checks and emit a human visual-QA checklist."""
    ir = DesignIR.model_validate_json(ir_file.read_text(encoding="utf-8"))
    report = audit_design_ir(ir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(report.model_dump_json(indent=2))
    if report.status == "blocked":
        raise typer.Exit(1)
\n\nif __name__ == "__main__":\n    app()\n

@app.command("compile-layout")
def compile_layout_command(
    graph_file: Path,
    pattern_id: str,
    catalog_file: Path = Path("visual_patterns/generali/insurance_layout_catalog.json"),
    geometry_file: Path = Path("visual_patterns/generali/layout_geometry.json"),
    output: Path = Path("build/design_ir/compiled-slide.json"),
    min_font_pt: float = 12,
):
    """Resolve semantic slots into editable DesignIR using versioned geometry tokens."""
    graph = InformationGraph.model_validate_json(graph_file.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    geometry = json.loads(geometry_file.read_text(encoding="utf-8"))
    plan = build_layout_plan(graph, catalog, pattern_id, geometry_catalog=geometry)
    if plan.geometry_status != "resolved":
        raise typer.BadParameter("Layout geometry is incomplete: " + "; ".join(plan.warnings))
    ir = layout_plan_to_design_ir(graph, plan, min_font_pt=min_font_pt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(ir.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    typer.echo(f"Compiled {ir.slide_id}: {len(ir.nodes)} nodes, {len(ir.relations)} relations -> {output}")




@app.command("compile-layout")
def compile_layout_command(
    graph_file: Path,
    pattern_id: str,
    catalog_file: Path = Path("visual_patterns/generali/insurance_layout_catalog.json"),
    geometry_file: Path = Path("visual_patterns/generali/layout_geometry.json"),
    output: Path = Path("build/design_ir/compiled-slide.json"),
    min_font_pt: float = 12,
):
    """Resolve semantic slots into editable DesignIR using versioned geometry tokens."""
    graph = InformationGraph.model_validate_json(graph_file.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    geometry = json.loads(geometry_file.read_text(encoding="utf-8"))
    plan = build_layout_plan(graph, catalog, pattern_id, geometry_catalog=geometry)
    if plan.geometry_status != "resolved":
        raise typer.BadParameter("Layout geometry is incomplete: " + "; ".join(plan.warnings))
    ir = layout_plan_to_design_ir(graph, plan, min_font_pt=min_font_pt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(ir.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    typer.echo(f"Compiled {ir.slide_id}: {len(ir.nodes)} nodes, {len(ir.relations)} relations -> {output}")


if __name__ == "__main__":
    app()
