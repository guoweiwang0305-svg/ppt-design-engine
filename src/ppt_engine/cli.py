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


if __name__ == "__main__":
    app()


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
