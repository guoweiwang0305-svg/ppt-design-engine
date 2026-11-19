"""OpenAI-compatible multimodal provider for rendered slide critique."""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .vision_adapter import VisionCritique


DEFAULT_TAXONOMY = [
    "composition_imbalance", "weak_visual_hierarchy", "chart_encoding_unclear",
    "chart_label_unreadable", "image_crop_poor", "information_overcrowded",
    "style_inconsistent", "alignment_inconsistent", "contrast_insufficient",
    "text_overflow", "decorative_noise", "narrative_focus_unclear",
]


class OpenAICompatibleVisionProvider:
    """Calls a chat-completions endpoint with a complete slide PNG."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        provider_name: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.base_url = (base_url or os.getenv("PDE_VISION_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.getenv("PDE_VISION_API_KEY", "")
        self.model = model or os.getenv("PDE_VISION_MODEL", "")
        self.provider_name = provider_name or os.getenv("PDE_VISION_PROVIDER", "openai-compatible")
        self.timeout = timeout
        if not self.base_url or not self.model:
            raise ValueError("Set PDE_VISION_API_BASE and PDE_VISION_MODEL.")
        if not self.api_key:
            raise ValueError("Set PDE_VISION_API_KEY; do not put API keys in the review UI.")

    def inspect(self, image_path: Path, context: dict[str, Any]) -> VisionCritique:
        image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
        prompt = (
            "You are a rigorous senior presentation visual critic. Inspect the COMPLETE slide. "
            "Do not infer defects from style preference alone. Use only these issue codes: "
            + ", ".join(DEFAULT_TAXONOMY)
            + ". Return a JSON object with keys summary and findings. Each finding must contain "
            "code, category (composition|hierarchy|chart_expression|image_crop|density|"
            "style_consistency|legibility|other), severity (blocker|major|minor|info), "
            "rationale, recommendation, confidence (0..1), and optional bbox "
            "[normalized_x, normalized_y, normalized_width, normalized_height]. "
            "No markdown fences. Avoid duplicate findings. Context: "
            + json.dumps(context, ensure_ascii=False)
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": "data:image/png;base64," + image_data,
                        "detail": "high",
                    }},
                ],
            }],
        }
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:2000]
            raise RuntimeError(f"Vision API HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Vision API connection failed: {exc}") from exc

        returned_model = raw.get("model") or self.model
        content = raw["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if part.get("type") == "text")
        parsed = json.loads(content)
        return VisionCritique(
            available=True,
            provider=self.provider_name,
            model=returned_model,
            image_path=str(image_path),
            summary=parsed.get("summary", ""),
            findings=parsed.get("findings", []),
            limitations=parsed.get("limitations", []),
            human_review_required=True,
        )
