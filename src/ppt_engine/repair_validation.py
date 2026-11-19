"""Transactional acceptance gate for before/after visual repairs."""
from __future__ import annotations

from collections import Counter
from typing import Any

from .models import StrictModel


SEVERITY_WEIGHT = {"blocker": 100, "major": 20, "minor": 5, "info": 0}


class RepairComparison(StrictModel):
    accepted: bool
    baseline_score: int
    candidate_score: int
    improved_issue_codes: list[str]
    regressed_issue_codes: list[str]
    unchanged_issue_codes: list[str]
    reason: str
    requires_human_review: bool = True


def _findings(report: Any) -> list[dict]:
    if hasattr(report, "model_dump"):
        report = report.model_dump(mode="json")
    if not isinstance(report, dict):
        raise TypeError("Critic report must be a mapping or Pydantic model")
    result = list(report.get("findings", []))
    for key in ("rendered_visual_critique", "ocr_critique", "vision_critique"):
        section = report.get(key) or {}
        result.extend(section.get("findings", []))
    return [item for item in result if item.get("severity") != "info"]


def _score(items: list[dict]) -> int:
    return sum(SEVERITY_WEIGHT.get(item.get("severity", "info"), 0) for item in items)


def compare_repair_reports(baseline: Any, candidate: Any) -> RepairComparison:
    """Accept only net improvement with no new blocker/major regression.

    Findings are compared by (code, node_ids); repeated instances are counted.
    An unavailable vision provider contributes no score and is never treated as
    a clean bill of health. Human review remains mandatory after automated pass.
    """
    before, after = _findings(baseline), _findings(candidate)
    key = lambda x: (x.get("code", "unknown"), tuple(sorted(x.get("node_ids", []))))
    b = Counter(key(x) for x in before)
    a = Counter(key(x) for x in after)
    improved = sorted({k[0] for k in b if b[k] > a[k]})
    regressed = sorted({k[0] for k in a if a[k] > b[k]})
    unchanged = sorted({k[0] for k in b if b[k] == a[k] and b[k] > 0})
    before_score, after_score = _score(before), _score(after)
    severe_regression = any(
        item.get("severity") in ("blocker", "major") and a[key(item)] > b[key(item)]
        for item in after
    )
    accepted = after_score < before_score and not severe_regression
    if severe_regression:
        reason = "Rejected: candidate introduces or increases a blocker/major finding."
    elif after_score >= before_score:
        reason = "Rejected: candidate does not reduce the weighted diagnostic burden."
    else:
        reason = "Accepted as a candidate: weighted issues decreased with no severe regression."
    return RepairComparison(
        accepted=accepted, baseline_score=before_score, candidate_score=after_score,
        improved_issue_codes=improved, regressed_issue_codes=regressed,
        unchanged_issue_codes=unchanged, reason=reason,
    )
