import json
from pathlib import Path

import pytest

from ppt_engine.vision_adapter import VisionCritique, VisionFinding
from ppt_engine.vision_benchmark_runner import run_manifest


class FakeProvider:
    def __init__(self, models=None):
        self.models = models or ["vision-v1", "vision-v1"]

    def inspect(self, image_path: Path, context: dict) -> VisionCritique:
        model = self.models.pop(0)
        return VisionCritique(
            available=True,
            provider="test-provider",
            model=model,
            image_path=str(image_path),
            findings=[
                VisionFinding(
                    code="information_overcrowded",
                    category="density",
                    severity="major",
                    rationale="Dense content.",
                    recommendation="Split the slide.",
                    confidence=0.9,
                )
            ],
        )


def _manifest(tmp_path: Path, statuses=None):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    cases = []
    for i in range(2):
        name = f"slide-{i}.png"
        (image_dir / name).write_bytes(b"fake-png")
        cases.append({
            "case_id": f"GCL:slide-{i+1:02d}",
            "source_family": "GCL",
            "slide_type": "chart",
            "image_file": name,
            "review_status": (statuses or ["reviewed", "reviewed"])[i],
            "reviewer_id": "expert",
            "expected_issue_codes": ["information_overcrowded"] if i == 0 else [],
        })
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "dataset_id": "test",
        "issue_code_taxonomy": ["information_overcrowded"],
        "cases": cases,
    }), encoding="utf-8")
    return manifest, image_dir


def test_run_manifest_scores_all_cases_and_persists_predictions(tmp_path):
    manifest, image_dir = _manifest(tmp_path)
    output = tmp_path / "out" / "benchmark.json"
    report = run_manifest(manifest, image_dir, output, provider=FakeProvider())
    assert report["case_count"] == 2
    assert report["score"]["true_positive"] == 1
    assert report["score"]["false_positive"] == 1
    assert report["score"]["false_negative"] == 0
    assert report["error_analysis"]["false_positive_by_page_type"][0] == {
        "name": "GCL::chart", "count": 1
    }
    assert report["error_analysis"]["false_negative_by_page_type"] == []
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert len(saved["predictions"]) == 2
    assert saved["provider"] == "test-provider"
    assert saved["model"] == "vision-v1"


def test_run_manifest_blocks_pending_expert_labels(tmp_path):
    manifest, image_dir = _manifest(tmp_path, ["reviewed", "pending_expert_review"])
    with pytest.raises(ValueError, match="Expert review incomplete"):
        run_manifest(manifest, image_dir, tmp_path / "out.json", provider=FakeProvider())


def test_run_manifest_rejects_model_identity_change(tmp_path):
    manifest, image_dir = _manifest(tmp_path)
    with pytest.raises(RuntimeError, match="Model identity changed"):
        run_manifest(
            manifest, image_dir, tmp_path / "out.json",
            provider=FakeProvider(["vision-v1", "vision-v2"]),
        )


def test_run_manifest_requires_opt_in_for_provisional_labels(tmp_path):
    manifest, image_dir = _manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["cases"][0]["review_provenance"] = "provisional GPT-6 review"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="provisional AI-assisted labels"):
        run_manifest(manifest, image_dir, tmp_path / "out.json", provider=FakeProvider())


def test_run_manifest_marks_exploratory_provisional_scores(tmp_path):
    manifest, image_dir = _manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["cases"][0]["review_provenance"] = "provisional GPT-6 review"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    report = run_manifest(
        manifest, image_dir, tmp_path / "out.json",
        provider=FakeProvider(), allow_provisional_labels=True,
    )
    assert report["label_quality"] == "provisional_ai_assisted"
    assert report["benchmark_validity"] == "exploratory_only"


def test_run_manifest_rejects_unknown_issue_codes(tmp_path):
    manifest, image_dir = _manifest(tmp_path)
    class UnknownCodeProvider:
        def inspect(self, image_path: Path, context: dict) -> VisionCritique:
            return VisionCritique(
                available=True, provider="test-provider", model="vision-v1",
                image_path=str(image_path),
                findings=[VisionFinding(
                    code="invented_code", category="other", severity="minor",
                    rationale="Unknown", recommendation="Ignore", confidence=0.5,
                )],
            )
    with pytest.raises(ValueError, match="outside the dataset taxonomy"):
        run_manifest(manifest, image_dir, tmp_path / "out.json", provider=UnknownCodeProvider())
