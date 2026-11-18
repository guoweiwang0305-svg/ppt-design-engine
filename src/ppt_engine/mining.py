"""Deterministic visual-pattern mining from P0.7 parsed PPTX datasets.

This module mines recurring structural signatures. It does not claim learned aesthetics:
expert review remains the authority for approving reusable patterns.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import Field

from .models import StrictModel


class SlideFeatures(StrictModel):
    reference_id: str
    source_file: str
    slide_number: int
    element_count: int
    text_count: int
    shape_count: int
    image_count: int
    connector_count: int
    density: str
    composition: str
    alignment_signature: str
    color_signature: list[str] = Field(default_factory=list)
    typography_signature: list[str] = Field(default_factory=list)
    structural_signature: str


class MinedPattern(StrictModel):
    pattern_id: str
    name: str
    family: str
    frequency: int
    reference_slides: list[str]
    feature_summary: dict[str, Any]
    expert_status: str = "unreviewed"
    confidence: float = 0.0


class PatternReview(StrictModel):
    pattern_id: str
    decision: str
    reviewer: str = "expert"
    reason_codes: list[str] = Field(default_factory=list)
    notes: str = ""
    revised_name: str | None = None
    revised_family: str | None = None


def _hex_colors(slide: dict[str, Any]) -> list[str]:
    colors: set[str] = set()
    for element in slide.get("elements", []):
        for section in ("fill", "line"):
            color = (element.get(section) or {}).get("color")
            if isinstance(color, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                colors.add(color.upper())
        for run in (element.get("text_style") or {}).get("runs", []):
            color = run.get("color")
            if isinstance(color, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                colors.add(color.upper())
    return sorted(colors)


def _composition(elements: list[dict[str, Any]]) -> str:
    if not elements:
        return "empty"
    centers = []
    for e in elements:
        b = e.get("bbox", {})
        centers.append((float(b.get("x", 0)) + float(b.get("width", 0)) / 2,
                        float(b.get("y", 0)) + float(b.get("height", 0)) / 2))
    xs = [p[0] for p in centers]
    ys = [p[1] for p in centers]
    xspread = max(xs) - min(xs) if xs else 0
    yspread = max(ys) - min(ys) if ys else 0
    if xspread > 0.62 and yspread < 0.35:
        return "horizontal"
    if yspread > 0.52 and xspread < 0.42:
        return "vertical"
    if xspread > 0.55 and yspread > 0.48:
        return "distributed"
    return "central_or_grid"


def extract_slide_features(parsed: dict[str, Any]) -> list[SlideFeatures]:
    result: list[SlideFeatures] = []
    source = str(parsed.get("source_file", "unknown"))
    for slide in parsed.get("slides", []):
        elements = slide.get("elements", [])
        text_count = sum(bool(e.get("text", "").strip()) for e in elements)
        shape_count = sum(e.get("kind") in {"shape", "group"} for e in elements)
        image_count = sum(e.get("kind") == "image" for e in elements)
        connector_count = int(slide.get("connector_count", len(slide.get("connectors", []))))
        n = len(elements)
        density = "low" if n < 8 else "medium" if n < 18 else "high"
        composition = _composition(elements)
        align_bins = []
        for e in elements:
            x = float(e.get("bbox", {}).get("x", 0))
            align_bins.append(str(round(x / 0.05) * 5))
        alignment = ",".join(sorted(align_bins))
        colors = _hex_colors(slide)
        fonts = sorted({str(r.get("font_name")) for e in elements
                        for r in (e.get("text_style") or {}).get("runs", [])
                        if r.get("font_name")})
        typography = sorted({str(r.get("font_size_pt")) for e in elements
                              for r in (e.get("text_style") or {}).get("runs", [])
                              if r.get("font_size_pt") is not None})
        signature = "|".join((composition, density, str(min(text_count, 5)),
                              str(min(shape_count, 8)), str(min(image_count, 4)),
                              str(min(connector_count, 8))))
        result.append(SlideFeatures(
            reference_id=f"{source}:slide-{slide.get('slide_number')}",
            source_file=source, slide_number=int(slide.get("slide_number", 0)),
            element_count=n, text_count=text_count, shape_count=shape_count,
            image_count=image_count, connector_count=connector_count,
            density=density, composition=composition,
            alignment_signature=alignment, color_signature=colors,
            typography_signature=fonts + typography,
            structural_signature=signature,
        ))
    return result


def mine_patterns(parsed_files: list[str | Path], min_frequency: int = 2) -> list[MinedPattern]:
    """Cluster slide feature signatures and emit reviewable candidate patterns."""
    buckets: dict[str, list[SlideFeatures]] = defaultdict(list)
    for file in parsed_files:
        data = json.loads(Path(file).read_text(encoding="utf-8"))
        for feature in extract_slide_features(data):
            buckets[feature.structural_signature].append(feature)
    mined: list[MinedPattern] = []
    for signature, members in sorted(buckets.items()):
        if len(members) < min_frequency:
            continue
        first = members[0]
        family = first.composition
        pattern_id = f"mined.{family}.{len(mined)+1:03d}"
        mined.append(MinedPattern(
            pattern_id=pattern_id,
            name=f"{family.replace('_', ' ').title()} / {first.density} density",
            family=family,
            frequency=len(members),
            reference_slides=[m.reference_id for m in members],
            feature_summary={
                "structural_signature": signature,
                "density": first.density,
                "composition": family,
                "avg_elements": round(sum(m.element_count for m in members) / len(members), 2),
                "common_colors": sorted(set.intersection(*(set(m.color_signature) for m in members))) if members else [],
                "font_signatures": sorted(set.intersection(*(set(m.typography_signature) for m in members))) if members else [],
            },
            confidence=round(min(0.95, 0.45 + 0.1 * (len(members) - 1)), 2),
        ))
    return sorted(mined, key=lambda p: (-p.frequency, p.pattern_id))


def save_pattern_review(review: PatternReview, ledger_path: str | Path) -> Path:
    """Append-only expert review log; original decisions are never overwritten."""
    target = Path(ledger_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(review.model_dump_json() + "\n")
    return target


def apply_pattern_reviews(patterns: list[MinedPattern], ledger_path: str | Path) -> list[MinedPattern]:
    path = Path(ledger_path)
    if not path.exists():
        return patterns
    reviews = [PatternReview.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    latest: dict[str, PatternReview] = {}
    for review in reviews:
        latest[review.pattern_id] = review
    result = []
    for pattern in patterns:
        review = latest.get(pattern.pattern_id)
        if review is None:
            result.append(pattern)
            continue
        status = {"accept": "approved", "reject": "rejected", "revise": "revision_required"}.get(review.decision, "unreviewed")
        result.append(pattern.model_copy(update={
            "expert_status": status,
            "name": review.revised_name or pattern.name,
            "family": review.revised_family or pattern.family,
        }))
    return result
