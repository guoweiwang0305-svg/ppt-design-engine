"""Human-labeled benchmark scoring for visual critic calibration."""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from .models import StrictModel


class VisualBenchmarkCase(StrictModel):
    case_id: str
    slide_type: str
    source_family: str = ""
    image_file: str = ""
    review_status: Literal["pending_expert_review", "reviewed"] = "reviewed"
    reviewer_id: str = ""
    expected_issue_codes: list[str] = Field(default_factory=list)
    observed_issue_codes: list[str] = Field(default_factory=list)
    reviewer_notes: str = ""


class BenchmarkScore(StrictModel):
    cases: int
    pending_cases: int = 0
    true_positive: int
    false_positive: int
    false_negative: int
    precision: float
    recall: float
    f1: float
    false_positive_codes: list[str] = Field(default_factory=list)
    missed_issue_codes: list[str] = Field(default_factory=list)
    by_slide_type: dict[str, dict] = Field(default_factory=dict)
    by_source_and_slide_type: dict[str, dict] = Field(default_factory=dict)


def _metrics(counts: dict[str, int]) -> dict[str, float | int]:
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]
    precision = tp / (tp + fp) if tp + fp else (1.0 if fn == 0 else 0.0)
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        **counts,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def score_visual_benchmark(cases: list[VisualBenchmarkCase]) -> BenchmarkScore:
    tp = 0
    fp = 0
    fn = 0
    false_positive_codes: list[str] = []
    missed_codes: list[str] = []
    groups: dict[str, dict[str, int]] = {}
    source_groups: dict[str, dict[str, int]] = {}

    reviewed_cases = [case for case in cases if case.review_status == "reviewed"]

    for case in reviewed_cases:
        expected = set(case.expected_issue_codes)
        observed = set(case.observed_issue_codes)
        case_tp = len(expected & observed)
        case_fp = len(observed - expected)
        case_fn = len(expected - observed)

        tp += case_tp
        fp += case_fp
        fn += case_fn
        false_positive_codes.extend(sorted(observed - expected))
        missed_codes.extend(sorted(expected - observed))

        slide_group = groups.setdefault(
            case.slide_type, {"tp": 0, "fp": 0, "fn": 0}
        )
        slide_group["tp"] += case_tp
        slide_group["fp"] += case_fp
        slide_group["fn"] += case_fn

        source_key = f"{case.source_family or 'unspecified'}::{case.slide_type}"
        source_group = source_groups.setdefault(
            source_key, {"tp": 0, "fp": 0, "fn": 0}
        )
        source_group["tp"] += case_tp
        source_group["fp"] += case_fp
        source_group["fn"] += case_fn

    total = _metrics({"tp": tp, "fp": fp, "fn": fn})
    by_slide_type = {name: _metrics(counts) for name, counts in groups.items()}
    by_source_and_slide_type = {
        name: _metrics(counts) for name, counts in source_groups.items()
    }

    return BenchmarkScore(
        cases=len(reviewed_cases),
        pending_cases=len(cases) - len(reviewed_cases),
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        precision=float(total["precision"]),
        recall=float(total["recall"]),
        f1=float(total["f1"]),
        false_positive_codes=false_positive_codes,
        missed_issue_codes=missed_codes,
        by_slide_type=by_slide_type,
        by_source_and_slide_type=by_source_and_slide_type,
    )
