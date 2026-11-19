"""Human-labeled benchmark scoring for visual critic calibration."""
from __future__ import annotations

from pydantic import Field
from .models import StrictModel


class VisualBenchmarkCase(StrictModel):
    case_id: str
    slide_type: str
    expected_issue_codes: list[str] = Field(default_factory=list)
    observed_issue_codes: list[str] = Field(default_factory=list)
    reviewer_notes: str = ""


class BenchmarkScore(StrictModel):
    cases: int
    true_positive: int
    false_positive: int
    false_negative: int
    precision: float
    recall: float
    f1: float
    false_positive_codes: list[str] = Field(default_factory=list)
    missed_issue_codes: list[str] = Field(default_factory=list)
    by_slide_type: dict[str, dict] = Field(default_factory=dict)


def score_visual_benchmark(cases: list[VisualBenchmarkCase]) -> BenchmarkScore:
    tp=fp=fn=0
    false_positive_codes=[]
    missed_codes=[]
    groups: dict[str,dict[str,int]]={}
    for case in cases:
        expected=set(case.expected_issue_codes)
        observed=set(case.observed_issue_codes)
        ctp=len(expected & observed)
        cfp=len(observed - expected)
        cfn=len(expected - observed)
        tp+=ctp; fp+=cfp; fn+=cfn
        false_positive_codes.extend(sorted(observed-expected))
        missed_codes.extend(sorted(expected-observed))
        group=groups.setdefault(case.slide_type,{"tp":0,"fp":0,"fn":0})
        group["tp"]+=ctp; group["fp"]+=cfp; group["fn"]+=cfn
    precision=tp/(tp+fp) if tp+fp else (1.0 if fn==0 else 0.0)
    recall=tp/(tp+fn) if tp+fn else 1.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    by_type={}
    for name,counts in groups.items():
        p=counts["tp"]/(counts["tp"]+counts["fp"]) if counts["tp"]+counts["fp"] else 1.0
        r=counts["tp"]/(counts["tp"]+counts["fn"]) if counts["tp"]+counts["fn"] else 1.0
        by_type[name]={**counts,"precision":round(p,4),"recall":round(r,4),
                       "f1":round(2*p*r/(p+r),4) if p+r else 0.0}
    return BenchmarkScore(cases=len(cases),true_positive=tp,false_positive=fp,
        false_negative=fn,precision=round(precision,4),recall=round(recall,4),
        f1=round(f1,4),false_positive_codes=false_positive_codes,
        missed_issue_codes=missed_codes,by_slide_type=by_type)
