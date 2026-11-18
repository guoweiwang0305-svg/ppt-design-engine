"""Editable PPTX reference parser.

Extracts native PowerPoint geometry and styling. It does not infer business semantics
from visual proximity; connector endpoints are retained as geometric evidence only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor

from .reverse_engineering import (
    BoundingBox, Connector, ReferenceVisualPage, VisualElement,
)


def _rgb(color: Any) -> str | None:
    try:
        rgb = color.rgb
        if isinstance(rgb, RGBColor):
            return f"#{rgb}"
    except (AttributeError, TypeError, ValueError):
        pass
    return None


def _font_details(shape: Any) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    paragraphs: list[dict[str, Any]] = []
    if not getattr(shape, "has_text_frame", False):
        return {"paragraphs": paragraphs, "runs": runs}
    for paragraph in shape.text_frame.paragraphs:
        paragraphs.append({
            "text": paragraph.text,
            "level": paragraph.level,
            "alignment": str(paragraph.alignment) if paragraph.alignment is not None else None,
        })
        for run in paragraph.runs:
            font = run.font
            runs.append({
                "text": run.text,
                "font_name": font.name,
                "font_size_pt": font.size.pt if font.size else None,
                "bold": font.bold,
                "italic": font.italic,
                "underline": font.underline,
                "color": _rgb(font.color),
            })
    return {"paragraphs": paragraphs, "runs": runs}


def _fill_details(shape: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"type": None, "color": None, "transparency": None}
    try:
        fill = shape.fill
        result["type"] = str(fill.type) if fill.type is not None else None
        if fill.type is not None:
            result["color"] = _rgb(fill.fore_color)
    except (AttributeError, TypeError, ValueError):
        pass
    return result


def _line_details(shape: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"color": None, "width_pt": None, "dash_style": None}
    try:
        line = shape.line
        result["color"] = _rgb(line.color)
        result["width_pt"] = line.width.pt if line.width else None
        result["dash_style"] = str(line.dash_style) if line.dash_style else None
    except (AttributeError, TypeError, ValueError):
        pass
    return result


def _shape_kind(shape: Any) -> str:
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        return "group"
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return "image"
    if shape.shape_type == MSO_SHAPE_TYPE.LINE or getattr(shape, "is_connector", False):
        return "line"
    if getattr(shape, "has_text_frame", False) and shape.text.strip():
        return "text"
    return "shape"


def parse_pptx(path: str | Path) -> dict[str, Any]:
    """Parse every slide into normalized geometry plus editable style metadata."""
    source = Path(path)
    prs = Presentation(str(source))
    canvas_w, canvas_h = prs.slide_width, prs.slide_height
    output: dict[str, Any] = {
        "source_file": source.name,
        "canvas": {"width_emu": canvas_w, "height_emu": canvas_h,
                   "width_inches": canvas_w / 914400, "height_inches": canvas_h / 914400},
        "slides": [],
        "parser": {"name": "pptx-native", "version": "0.1.0",
                   "semantic_inference": "disabled"},
    }
    for slide_index, slide in enumerate(prs.slides, start=1):
        elements: list[dict[str, Any]] = []
        connectors: list[dict[str, Any]] = []
        visual_elements: list[VisualElement] = []
        connector_index = 0

        def visit(shapes: Any, parent_group: str | None = None) -> None:
            nonlocal connector_index
            for shape in shapes:
                sid = str(shape.shape_id)
                kind = _shape_kind(shape)
                bbox = {
                    "x": shape.left / canvas_w,
                    "y": shape.top / canvas_h,
                    "width": shape.width / canvas_w,
                    "height": shape.height / canvas_h,
                }
                text = shape.text if getattr(shape, "has_text_frame", False) else ""
                if kind == "line":
                    connector_index += 1
                    connectors.append({
                        "connector_id": f"s{slide_index}-connector-{connector_index}",
                        "shape_id": sid,
                        "bbox": bbox,
                        "start": {"x": bbox["x"], "y": bbox["y"]},
                        "end": {"x": bbox["x"] + bbox["width"],
                                "y": bbox["y"] + bbox["height"]},
                        "line": _line_details(shape),
                        "semantic_relation": None,
                        "semantic_confidence": 0.0,
                    })
                else:
                    element = {
                        "element_id": f"s{slide_index}-shape-{sid}",
                        "shape_id": sid,
                        "name": shape.name,
                        "kind": kind,
                        "bbox": bbox,
                        "rotation": float(shape.rotation),
                        "z_index": len(elements),
                        "parent_group": parent_group,
                        "text": text,
                        "text_style": _font_details(shape),
                        "fill": _fill_details(shape),
                        "line": _line_details(shape),
                        "is_placeholder": bool(getattr(shape, "is_placeholder", False)),
                        "visual_weight": 0.5,
                    }
                    if kind == "image":
                        element["image"] = {
                            "width": shape.width, "height": shape.height,
                            "crop_left": float(shape.crop_left),
                            "crop_right": float(shape.crop_right),
                            "crop_top": float(shape.crop_top),
                            "crop_bottom": float(shape.crop_bottom),
                        }
                    elements.append(element)
                    visual_elements.append(VisualElement(
                        element_id=element["element_id"], kind=kind,
                        bbox=BoundingBox(**bbox), text=text or None,
                        parent_group=parent_group, z_index=element["z_index"],
                        visual_weight=0.5, is_decorative=False,
                        confidence=1.0,
                    ))
                if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                    visit(shape.shapes, parent_group=sid)

        visit(slide.shapes)
        # Preserve geometric connectors separately. Endpoint-to-node association is
        # intentionally not guessed in this parser; downstream adapters can resolve it.
        page = ReferenceVisualPage(
            reference_id=f"{source.stem}:slide-{slide_index}",
            canvas_width=canvas_w / 914400,
            canvas_height=canvas_h / 914400,
            elements=visual_elements,
            connectors=[],
            hierarchy=[],
        )
        output["slides"].append({
            "slide_number": slide_index,
            "reference_visual_page": page.model_dump(mode="json"),
            "elements": elements,
            "connectors": connectors,
            "element_count": len(elements),
            "connector_count": len(connectors),
        })
    return output


def parse_pptx_to_json(source: str | Path, destination: str | Path) -> Path:
    result = parse_pptx(source)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
