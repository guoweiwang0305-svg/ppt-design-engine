"""Command-line interface."""
from pathlib import Path
import json
import typer
from .models import DesignIR, PageStatus
from .orchestrator import Orchestrator
from .ledger import DataLedger
from .renderer import render_pptx, export_pdf, export_pngs

app = typer.Typer(help="PPT Design Engine — design intelligence and rendering tools")
project_app = typer.Typer(help="Project lifecycle commands")
ledger_app = typer.Typer(help="DataLedger commands")
app.add_typer(project_app, name="project")
app.add_typer(ledger_app, name="ledger")


@app.command()
def validate(ir_file: Path = typer.Argument(..., exists=True, readable=True)):
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
