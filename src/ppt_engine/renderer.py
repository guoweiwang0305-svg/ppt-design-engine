"""Minimal native PPTX renderer. Visual QA/export tools are external executables."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.util import Inches, Pt
from .models import DesignIR
from .ledger import DataLedger
from .advanced_critic import route_relations_orthogonal


def _rgb(value: str) -> RGBColor:
    raw = value.lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {value!r}")
    return RGBColor(*(int(raw[i:i+2], 16) for i in (0, 2, 4)))


def render_pptx(ir: DesignIR, output: str | Path, ledger: DataLedger | None = None) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(ir.canvas.width if ir.canvas.unit == "in" else ir.canvas.width / 72)
    prs.slide_height = Inches(ir.canvas.height if ir.canvas.unit == "in" else ir.canvas.height / 72)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # Route semantic relationships before nodes so nodes remain in the foreground.
    scale = 1 if ir.canvas.unit == "in" else (1 / 72 if ir.canvas.unit == "pt" else 1 / 96)
    routed = {route.relation_id: route for route in route_relations_orthogonal(ir)}
    for relation in ir.relations:
        route = routed.get(relation.id)
        if route is None or route.status != "routed":
            # Do not draw a connector through an obstacle when routing failed.
            continue
        for first, second in zip(route.points, route.points[1:]):
            x1, y1 = first[0] * scale, first[1] * scale
            x2, y2 = second[0] * scale, second[1] * scale
            if abs(x2-x1) + abs(y2-y1) < 1e-8:
                continue
            connector = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
            )
            connector.line.color.rgb = _rgb("#B7B7B7")
            connector.line.width = Pt(1.1)
    for node in ir.nodes:
        if node.geometry is None:
            raise ValueError(f"Node {node.id!r} has no geometry; renderer never guesses layout")
        g = node.geometry
        scale = 1 if ir.canvas.unit == "in" else (1 / 72 if ir.canvas.unit == "pt" else 1 / 96)
        x, y, w, h = (v * scale for v in (g.x, g.y, g.width, g.height))
        if node.visual_type in {"rect", "ellipse"}:
            from pptx.enum.shapes import MSO_SHAPE
            shape_type = MSO_SHAPE.RECTANGLE if node.visual_type == "rect" else MSO_SHAPE.OVAL
            shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
            shape.fill.solid()
            shape.fill.fore_color.rgb = _rgb(node.fill or "#F5E8EC")
            shape.line.fill.background()
            if not node.text:
                continue
            frame = shape.text_frame
        else:
            shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
            frame = shape.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.margin_left = Inches(0.06)
        frame.margin_right = Inches(0.06)
        frame.margin_top = Inches(0.03)
        frame.margin_bottom = Inches(0.03)
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = frame.paragraphs[0]
        p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[node.align]
        run = p.add_run()
        if node.data_ref:
            if ledger is None:
                raise ValueError(f"Node {node.id!r} references {node.data_ref!r}; provide a DataLedger")
            entry = ledger.resolve(node.data_ref)
            run.text = f"{entry.value} {entry.unit}".strip()
        else:
            run.text = node.text
        run.font.size = Pt(node.font_size_pt)
        run.font.color.rgb = _rgb(node.color)
        run.font.name = "Aptos"
    prs.save(output)
    return output


def export_pdf(pptx_path: str | Path, output_dir: str | Path) -> Path:
    office = shutil.which("libreoffice") or shutil.which("soffice")
    if not office:
        raise RuntimeError("LibreOffice is required for PDF export. Install libreoffice and retry.")
    pptx_path = Path(pptx_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [office, "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(pptx_path)],
        capture_output=True, text=True, check=False,
    )
    pdf = output_dir / f"{pptx_path.stem}.pdf"
    if result.returncode != 0 or not pdf.exists():
        raise RuntimeError(f"PDF export failed: {result.stderr or result.stdout}")
    return pdf


def export_pngs(pdf_path: str | Path, output_dir: str | Path, dpi: int = 160) -> list[Path]:
    converter = shutil.which("pdftoppm")
    if not converter:
        raise RuntimeError("Poppler pdftoppm is required for PNG export. Install poppler-utils.")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "slide"
    result = subprocess.run(
        [converter, "-png", "-r", str(dpi), str(Path(pdf_path).resolve()), str(prefix)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"PNG export failed: {result.stderr or result.stdout}")
    return sorted(output_dir.glob("slide-*.png"))
