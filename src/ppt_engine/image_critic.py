"""Rendered PNG visual analysis using deterministic raster measurements.

This is a perceptual preflight, not OCR or a learned vision model. It measures
ink distribution inside DesignIR regions, edge crowding, contrast proxies and
global visual balance while keeping every finding traceable to a region/node.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from PIL import Image, ImageStat
from pydantic import Field

from .models import DesignIR, StrictModel


class RegionVisualMetric(StrictModel):
    node_id: str
    pixel_box: tuple[int, int, int, int]
    ink_ratio: float
    luminance_spread: float
    ink_bbox_ratio: tuple[float, float, float, float] | None = None
    touches_region_edge: bool = False
    status: Literal["ok", "sparse", "dense", "edge_crowded", "low_contrast"]


class VisualFinding(StrictModel):
    code: str
    severity: Literal["blocker", "major", "minor", "info"]
    node_ids: list[str] = Field(default_factory=list)
    diagnosis: str
    recommendation: str


class RenderedVisualCritique(StrictModel):
    image_path: str
    width_px: int
    height_px: int
    analyzed_regions: int
    global_ink_ratio: float
    visual_center: tuple[float, float]
    quadrant_ink_ratios: dict[str, float]
    region_metrics: list[RegionVisualMetric] = Field(default_factory=list)
    findings: list[VisualFinding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=lambda: [
        "No OCR: text identity, spelling, clipping of individual glyphs and reading order are not verified.",
        "No learned vision model: aesthetic quality, image meaning, chart correctness and brand fidelity require human review.",
        "Raster thresholds are heuristic and may need calibration for dark backgrounds, photography and full-bleed designs.",
    ])


def _luminance(image: Image.Image) -> Image.Image:
    return image.convert("L")


def _ink_mask(image: Image.Image, threshold: int = 218) -> Image.Image:
    return _luminance(image).point(lambda value: 255 if value < threshold else 0)


def _ratio(mask: Image.Image) -> float:
    hist = mask.histogram()
    total = max(1, mask.width * mask.height)
    return hist[255] / total


def _bbox_ratio(mask: Image.Image) -> tuple[float, float, float, float] | None:
    bbox = mask.getbbox()
    if bbox is None:
        return None
    left, top, right, bottom = bbox
    return (
        round(left / max(1, mask.width), 4),
        round(top / max(1, mask.height), 4),
        round(right / max(1, mask.width), 4),
        round(bottom / max(1, mask.height), 4),
    )


def analyze_rendered_png(ir: DesignIR, image_path: str | Path) -> RenderedVisualCritique:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(path)
    image = Image.open(path).convert("RGB")
    width, height = image.size
    # Use the rendered image's actual aspect ratio; DesignIR canvas coordinates
    # are scaled independently to avoid assumptions about a specific DPI.
    sx, sy = width / ir.canvas.width, height / ir.canvas.height
    full_mask = _ink_mask(image)
    global_ink = _ratio(full_mask)
    global_bbox = full_mask.getbbox()
    if global_bbox:
        cx = (global_bbox[0] + global_bbox[2] / 2) / width
        cy = (global_bbox[1] + global_bbox[3] / 2) / height
    else:
        cx = cy = 0.5

    quadrant_ratios = {}
    for name, box in {
        "top_left": (0, 0, width // 2, height // 2),
        "top_right": (width // 2, 0, width, height // 2),
        "bottom_left": (0, height // 2, width // 2, height),
        "bottom_right": (width // 2, height // 2, width, height),
    }.items():
        quadrant_ratios[name] = round(_ratio(full_mask.crop(box)), 5)

    metrics = []
    findings = []
    for node in ir.nodes:
        if node.geometry is None or node.visual_type != "text" or not node.text.strip():
            continue
        g = node.geometry
        left = max(0, min(width - 1, round(g.x * sx)))
        top = max(0, min(height - 1, round(g.y * sy)))
        right = max(left + 1, min(width, round((g.x + g.width) * sx)))
        bottom = max(top + 1, min(height, round((g.y + g.height) * sy)))
        crop = image.crop((left, top, right, bottom))
        mask = _ink_mask(crop)
        ink_ratio = _ratio(mask)
        lum = _luminance(crop)
        spread = ImageStat.Stat(lum).stddev[0]
        bbox = _bbox_ratio(mask)
        edge_touch = bool(bbox and (
            bbox[0] <= 0.015 or bbox[1] <= 0.015 or
            bbox[2] >= 0.985 or bbox[3] >= 0.985
        ))
        if edge_touch:
            status = "edge_crowded"
        elif spread < 9 and ink_ratio > 0.002:
            status = "low_contrast"
        elif ink_ratio > 0.42:
            status = "dense"
        elif ink_ratio < 0.001:
            status = "sparse"
        else:
            status = "ok"
        metrics.append(RegionVisualMetric(
            node_id=node.id, pixel_box=(left, top, right, bottom),
            ink_ratio=round(ink_ratio, 5), luminance_spread=round(spread, 2),
            ink_bbox_ratio=bbox, touches_region_edge=edge_touch, status=status,
        ))
        if edge_touch:
            findings.append(VisualFinding(
                code="rendered_text_near_region_edge", severity="major", node_ids=[node.id],
                diagnosis="Visible ink reaches the text region boundary; the text may be crowded or clipped.",
                recommendation="Increase text-box padding/height or reduce text volume; verify at 100% zoom.",
            ))
        elif status == "dense":
            findings.append(VisualFinding(
                code="rendered_region_ink_dense", severity="minor", node_ids=[node.id],
                diagnosis=f"High raster ink occupancy ({ink_ratio:.0%}) in this text region.",
                recommendation="Check line spacing and content density; prefer editing or splitting content over shrinking type.",
            ))
        elif status == "sparse":
            findings.append(VisualFinding(
                code="rendered_region_ink_sparse", severity="info", node_ids=[node.id],
                diagnosis="Very little dark ink was detected in the expected text region.",
                recommendation="Check whether text is invisible, incorrectly colored, absent from the render or intentionally blank.",
            ))
        elif status == "low_contrast":
            findings.append(VisualFinding(
                code="rendered_region_low_contrast", severity="major", node_ids=[node.id],
                diagnosis="Low luminance variation was detected in a region expected to contain text.",
                recommendation="Check foreground/background contrast and verify the text is legible in grayscale.",
            ))

    if global_ink < 0.002:
        findings.append(VisualFinding(
            code="rendered_page_near_blank", severity="blocker",
            diagnosis="The rendered page contains almost no dark pixel content.",
            recommendation="Check rendering, fonts, visibility and the generated PPTX before delivery.",
        ))
    if global_ink > 0.48:
        findings.append(VisualFinding(
            code="rendered_page_extremely_dense", severity="major",
            diagnosis=f"Global dark-pixel occupancy is unusually high ({global_ink:.0%}).",
            recommendation="Inspect page density and consider restructuring or splitting the information.",
        ))
    if global_bbox and (cx < 0.28 or cx > 0.72 or cy < 0.22 or cy > 0.78):
        findings.append(VisualFinding(
            code="visual_mass_off_center", severity="minor",
            diagnosis=f"Dark-pixel bounding-box center is at ({cx:.2f}, {cy:.2f}) of the page.",
            recommendation="Check whether the visual mass imbalance is intentional and supported by the composition.",
        ))

    return RenderedVisualCritique(
        image_path=str(path), width_px=width, height_px=height,
        analyzed_regions=len(metrics), global_ink_ratio=round(global_ink, 5),
        visual_center=(round(cx, 4), round(cy, 4)),
        quadrant_ink_ratios=quadrant_ratios, region_metrics=metrics,
        findings=findings,
    )
