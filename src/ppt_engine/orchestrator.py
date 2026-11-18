"""Small, explicit page lifecycle state machine."""
from __future__ import annotations
import json
import os
from pathlib import Path
from .models import PageRecord, PageStatus, ProjectState

TRANSITIONS: dict[PageStatus, set[PageStatus]] = {
    PageStatus.PLANNED: {PageStatus.CONTENT_APPROVED, PageStatus.CONTENT_REWORK},
    PageStatus.CONTENT_APPROVED: {PageStatus.DESIGN_APPROVED, PageStatus.DESIGN_REWORK},
    PageStatus.DESIGN_APPROVED: {PageStatus.RENDERED, PageStatus.RENDER_REWORK},
    PageStatus.RENDERED: {PageStatus.QA_PASSED, PageStatus.QA_REJECTED, PageStatus.RENDER_REWORK},
    PageStatus.QA_PASSED: {PageStatus.DELIVERED, PageStatus.DESIGN_REWORK},
    PageStatus.CONTENT_REWORK: {PageStatus.CONTENT_APPROVED},
    PageStatus.DESIGN_REWORK: {PageStatus.DESIGN_APPROVED},
    PageStatus.RENDER_REWORK: {PageStatus.RENDERED},
    PageStatus.QA_REJECTED: {PageStatus.DESIGN_REWORK, PageStatus.RENDER_REWORK},
    PageStatus.DELIVERED: set(),
}


class Orchestrator:
    def __init__(self, state_path: str | Path):
        self.path = Path(state_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> ProjectState:
        if self.path.exists():
            return ProjectState.model_validate_json(self.path.read_text(encoding="utf-8"))
        return ProjectState(project_id=self.path.parent.name or "project")

    def _save(self) -> None:
        self.state.revision += 1
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(self.state.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temp, self.path)

    def add_page(self, slide_id: str) -> PageRecord:
        if slide_id in self.state.pages:
            raise ValueError(f"Page {slide_id!r} already exists")
        record = PageRecord(slide_id=slide_id)
        self.state.pages[slide_id] = record
        self._save()
        return record

    def transition(self, slide_id: str, target: PageStatus, issue: str | None = None) -> PageRecord:
        if slide_id not in self.state.pages:
            raise KeyError(f"Unknown slide: {slide_id}")
        page = self.state.pages[slide_id]
        if target not in TRANSITIONS[page.status]:
            raise ValueError(f"Illegal page transition: {page.status.value} → {target.value}")
        page.status = target
        if issue:
            page.issues.append(issue)
        if target in {PageStatus.CONTENT_REWORK, PageStatus.DESIGN_REWORK,
                      PageStatus.RENDER_REWORK, PageStatus.QA_REJECTED}:
            page.version += 1
        self._save()
        return page
