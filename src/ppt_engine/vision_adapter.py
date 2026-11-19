"""Provider-neutral multimodal vision critic contract.

Deployment-specific providers inspect the complete rendered PNG. No API client,
credentials, endpoint or model is bundled in the core engine.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field

from .models import StrictModel


class VisionFinding(StrictModel):
    code: str
    category: Literal["composition", "hierarchy", "chart_expression", "image_crop",
                      "density", "style_consistency", "legibility", "other"]
    severity: Literal["blocker", "major", "minor", "info"]
    rationale: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    # Normalized [x, y, width, height] on the complete slide.
    bbox: tuple[float, float, float, float] | None = None
    node_ids: list[str] = Field(default_factory=list)


class VisionCritique(StrictModel):
    available: bool
    provider: str
    model: str | None = None
    image_path: str
    summary: str = ""
    findings: list[VisionFinding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    human_review_required: bool = True


class VisionCriticProvider(Protocol):
    """Provider must inspect the full PNG, not only crops or extracted OCR."""

    def inspect(self, image_path: Path, context: dict) -> VisionCritique:
        ...


class UnconfiguredVisionProvider:
    """Return an explicit unavailable state instead of fabricated model findings."""

    def inspect(self, image_path: Path, context: dict) -> VisionCritique:
        return VisionCritique(
            available=False, provider="unconfigured", image_path=str(image_path),
            summary="No multimodal vision provider is configured; no model judgment was made.",
            limitations=[
                "Configure a deployment-specific VisionCriticProvider.",
                "Send full-slide images only under an approved data-handling policy.",
            ],
        )


def inspect_with_provider(image_path: str | Path, context: dict,
                          provider: VisionCriticProvider | None = None) -> VisionCritique:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(path)
    return (provider or UnconfiguredVisionProvider()).inspect(path, context)
