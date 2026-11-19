"""Run one pinned multimodal vision provider over a labeled image manifest."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .openai_vision_provider import OpenAICompatibleVisionProvider
from .visual_benchmark import VisualBenchmarkCase, score_visual_benchmark


def run_manifest(
    manifest_file: str | Path,
    image_dir: str | Path,
    output_file: str | Path,
    provider: OpenAICompatibleVisionProvider | None = None,
    allow_provisional_labels: bool = False,
) -> dict[str, Any]:
    manifest_path = Path(manifest_file)
    image_root = Path(image_dir)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    pending = [c.get("case_id", "?") for c in cases if c.get("review_status") != "reviewed"]
    if pending:
        raise ValueError(
            f"Expert review incomplete: {len(pending)} pending cases; first: {', '.join(pending[:5])}"
        )
    provisional = any(
        "provisional" in str(case.get("review_provenance", "")).lower()
        or "GPT-6" in str(case.get("reviewer_id", ""))
        for case in cases
    )
    if provisional and not allow_provisional_labels:
        raise ValueError(
            "Manifest contains provisional AI-assisted labels. "
            "Human-adjudicate the labels or pass allow_provisional_labels=True "
            "for an explicitly exploratory run."
        )

    provider = provider or OpenAICompatibleVisionProvider()
    predictions: dict[str, dict[str, Any]] = {}
    identity: tuple[str, str] | None = None
    scored_cases: list[VisualBenchmarkCase] = []

    for case in cases:
        case_id = case["case_id"]
        image_path = image_root / case["image_file"]
        if not image_path.is_file():
            raise FileNotFoundError(f"{case_id}: image not found: {image_path}")
        context = {
            "case_id": case_id,
            "source_family": case.get("source_family", ""),
            "slide_type": case.get("slide_type", ""),
            "style_reference": (
                "GCL corporate brand style: restrained red, white, charcoal; assess style consistency."
                if case.get("source_family") == "GCL"
                else "AIA is an information-structure reference only; do not score it against GCL brand colors."
            ),
            "expert_labels_hidden": True,
        }
        result = provider.inspect(image_path, context)
        if not result.available or not result.provider or not result.model:
            raise RuntimeError(f"{case_id}: provider returned unavailable or missing identity.")
        current_identity = (result.provider, result.model)
        if identity is not None and current_identity != identity:
            raise RuntimeError(
                f"Model identity changed during batch: expected {identity}, got {current_identity}."
            )
        identity = current_identity
        predictions[case_id] = result.model_dump(mode="json")
        observed = sorted({finding.code for finding in result.findings})
        unknown_codes = sorted(set(observed) - set(payload.get("issue_code_taxonomy", [])))
        if unknown_codes:
            raise ValueError(
                f"{case_id}: model returned issue codes outside the dataset taxonomy: "
                f"{', '.join(unknown_codes)}"
            )
        scored_cases.append(VisualBenchmarkCase(
            case_id=case_id,
            slide_type=case.get("slide_type", "unspecified"),
            source_family=case.get("source_family", ""),
            image_file=case.get("image_file", ""),
            review_status="reviewed",
            reviewer_id=case.get("reviewer_id", ""),
            expected_issue_codes=case.get("expected_issue_codes", []),
            observed_issue_codes=observed,
            reviewer_notes=case.get("reviewer_notes", ""),
        ))

    score = score_visual_benchmark(scored_cases)
    false_positive_by_group: dict[str, int] = {}
    false_negative_by_group: dict[str, int] = {}
    false_positive_by_code: dict[str, int] = {}
    false_negative_by_code: dict[str, int] = {}
    for case in scored_cases:
        expected = set(case.expected_issue_codes)
        observed = set(case.observed_issue_codes)
        group = f"{case.source_family or 'unspecified'}::{case.slide_type}"
        false_positive_by_group[group] = false_positive_by_group.get(group, 0) + len(observed - expected)
        false_negative_by_group[group] = false_negative_by_group.get(group, 0) + len(expected - observed)
        for code in observed - expected:
            false_positive_by_code[code] = false_positive_by_code.get(code, 0) + 1
        for code in expected - observed:
            false_negative_by_code[code] = false_negative_by_code.get(code, 0) + 1

    def ranked_counts(values: dict[str, int]) -> list[dict[str, str | int]]:
        return [
            {"name": name, "count": count}
            for name, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))
        ]

    output = {
        "dataset_id": payload.get("dataset_id", "gcl-aia-35"),
        "provider": identity[0] if identity else "",
        "model": identity[1] if identity else "",
        "temperature": 0,
        "case_count": len(scored_cases),
        "label_quality": "provisional_ai_assisted" if provisional else "human_adjudicated",
        "benchmark_validity": "exploratory_only" if provisional else "gold_label_candidate",
        "predictions": predictions,
        "cases": [c.model_dump(mode="json") for c in scored_cases],
        "score": score.model_dump(mode="json"),
        "error_analysis": {
            "false_positive_by_page_type": ranked_counts(false_positive_by_group),
            "false_negative_by_page_type": ranked_counts(false_negative_by_group),
            "false_positive_issue_codes": ranked_counts(false_positive_by_code),
            "false_negative_issue_codes": ranked_counts(false_negative_by_code),
        },
    }
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
