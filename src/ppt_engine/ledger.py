"""Single-source-of-truth numeric ledger and cross-slide consistency checks."""
from __future__ import annotations
from pathlib import Path
from pydantic import Field
from .models import StrictModel


class LedgerEntry(StrictModel):
    id: str = Field(min_length=1)
    value: int | float | str
    unit: str
    definition: str
    source: str
    time: str
    context: str = ""


class DataLedger(StrictModel):
    entries: dict[str, LedgerEntry] = Field(default_factory=dict)

    def register(self, entry: LedgerEntry) -> None:
        existing = self.entries.get(entry.id)
        if existing and existing != entry:
            raise ValueError(f"Ledger ID {entry.id!r} already exists with a different value/definition")
        self.entries[entry.id] = entry

    def resolve(self, data_ref: str) -> LedgerEntry:
        try:
            return self.entries[data_ref]
        except KeyError as exc:
            raise KeyError(f"Unknown DataLedger reference: {data_ref}") from exc

    def validate_references(self, slide_refs: dict[str, list[str]]) -> list[str]:
        errors: list[str] = []
        for slide_id, refs in slide_refs.items():
            for ref in refs:
                if ref not in self.entries:
                    errors.append(f"{slide_id}: unknown data_ref {ref}")
        return errors

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> DataLedger:
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


def compare_slide_values(slide_values: dict[str, dict[str, int | float | str]]) -> list[str]:
    """Detect a repeated metric ID rendered with inconsistent values across pages."""
    seen: dict[str, tuple[int | float | str, str]] = {}
    issues: list[str] = []
    for slide_id, values in slide_values.items():
        for metric_id, value in values.items():
            if metric_id in seen and seen[metric_id][0] != value:
                old_value, old_slide = seen[metric_id]
                issues.append(
                    f"{metric_id}: {old_value!r} on {old_slide} conflicts with {value!r} on {slide_id}"
                )
            else:
                seen[metric_id] = (value, slide_id)
    return issues
