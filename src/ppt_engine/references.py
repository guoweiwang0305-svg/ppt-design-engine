"""Reference-slide reverse engineering intake and normalized design dataset."""
from __future__ import annotations
import hashlib
from pathlib import Path
from .models import StrictModel
from .intelligence import InformationGraph, VisualGrammar
from pydantic import Field


class ReferenceAnnotation(StrictModel):
    reference_id: str
    image_path: str
    image_sha256: str | None = None
    source_description: str = ""
    information_graph: InformationGraph
    visual_grammar: VisualGrammar
    inferred_pattern_ids: list[str] = Field(default_factory=list)
    analyst_notes: list[str] = Field(default_factory=list)
    confidence: float = 0.5

    def verify_image(self, root: str | Path = ".") -> str:
        path = Path(root) / self.image_path
        if not path.exists():
            raise FileNotFoundError(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if self.image_sha256 and digest != self.image_sha256:
            raise ValueError("Reference image checksum mismatch")
        return digest


def load_reference(path: str | Path) -> ReferenceAnnotation:
    return ReferenceAnnotation.model_validate_json(Path(path).read_text(encoding="utf-8"))


def export_reference_dataset(records: list[ReferenceAnnotation], output: str | Path) -> None:
    payload = [record.model_dump(mode="json") for record in records]
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    import json
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
